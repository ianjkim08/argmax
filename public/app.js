const strategySchemas = {
  moving_average_cross: [
    { key: "fast", label: "Fast window", value: 20, min: 1, step: 1 },
    { key: "slow", label: "Slow window", value: 100, min: 2, step: 1 },
  ],
  rsi_mean_reversion: [
    { key: "period", label: "RSI period", value: 14, min: 1, step: 1 },
    { key: "oversold", label: "Buy below", value: 30, min: 0, max: 99, step: 1 },
    { key: "exit_level", label: "Exit above", value: 50, min: 1, max: 100, step: 1 },
  ],
  bollinger_reversion: [
    { key: "period", label: "Band window", value: 20, min: 2, step: 1 },
    { key: "std_dev", label: "Std. deviations", value: 2, min: 0.1, step: 0.1 },
  ],
  momentum: [
    { key: "lookback", label: "Lookback", value: 126, min: 1, step: 1 },
    { key: "threshold", label: "Threshold", value: 0, step: 0.01 },
  ],
};

const strategyLabels = {
  moving_average_cross: "Moving Average Crossover",
  rsi_mean_reversion: "RSI Mean Reversion",
  bollinger_reversion: "Bollinger Reversion",
  momentum: "Price Momentum",
};

const form = document.querySelector("#backtest-form");
const strategySelect = document.querySelector("#strategy");
const parameterRoot = document.querySelector("#strategy-parameters");
const runButton = form.querySelector(".run-button");
const apiStatus = document.querySelector("#api-status");
const states = {
  empty: document.querySelector("#empty-state"),
  loading: document.querySelector("#loading-state"),
  error: document.querySelector("#error-state"),
  results: document.querySelector("#results"),
};
let latestResult = null;
let activeChart = "equity";

const API_OFFLINE_MESSAGE = 'Backtest API is not running. Stop the current server, run "argmax serve", and reload this page.';

function setApiStatus(message = "") {
  const hasError = Boolean(message);
  apiStatus.textContent = hasError
    ? message
    : "Market data supplied by Yahoo Finance. Research use only.";
  apiStatus.classList.toggle("api-error", hasError);
}

async function readJsonResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const body = await response.text();
  if (!contentType.toLowerCase().includes("application/json")) {
    throw new Error(body.trimStart().startsWith("<")
      ? API_OFFLINE_MESSAGE
      : "The backtest server returned an unsupported response. Restart Argmax and try again.");
  }

  let result;
  try {
    result = JSON.parse(body);
  } catch {
    throw new Error("The backtest server returned invalid JSON. Restart Argmax and try again.");
  }
  if (!response.ok) {
    throw new Error(result.error || "The server could not complete this backtest.");
  }
  return result;
}

async function checkApiHealth() {
  try {
    const response = await fetch("/api/health", { headers: { Accept: "application/json" } });
    const result = await readJsonResponse(response);
    if (result.status !== "ok") throw new Error(API_OFFLINE_MESSAGE);
    setApiStatus();
    return true;
  } catch (error) {
    setApiStatus(error.message === API_OFFLINE_MESSAGE ? error.message : API_OFFLINE_MESSAGE);
    return false;
  }
}

function showState(name) {
  Object.entries(states).forEach(([key, element]) => element.classList.toggle("hidden", key !== name));
  const activeState = states[name];
  if (
    activeState
    && window.gsap
    && !window.matchMedia("(prefers-reduced-motion: reduce)").matches
  ) {
    window.gsap.fromTo(
      activeState,
      { opacity: 0, y: 18 },
      { opacity: 1, y: 0, duration: 0.55, ease: "power3.out", clearProps: "transform" },
    );
  }
}

function renderParameters() {
  parameterRoot.replaceChildren();
  strategySchemas[strategySelect.value].forEach((parameter) => {
    const label = document.createElement("label");
    label.className = "field";
    const caption = document.createElement("span");
    caption.textContent = parameter.label;
    const input = document.createElement("input");
    input.type = "number";
    input.dataset.parameter = parameter.key;
    Object.entries(parameter).forEach(([key, value]) => {
      if (["key", "label"].includes(key)) return;
      input[key] = value;
    });
    label.append(caption, input);
    parameterRoot.append(label);
  });
}

function requestPayload() {
  const parameters = {};
  parameterRoot.querySelectorAll("input").forEach((input) => {
    parameters[input.dataset.parameter] = Number(input.value);
  });
  return {
    ticker: document.querySelector("#ticker").value,
    start: document.querySelector("#start").value,
    end: document.querySelector("#end").value,
    strategy: strategySelect.value,
    parameters,
    capital: Number(document.querySelector("#capital").value),
    position_size: Number(document.querySelector("#position-size").value) / 100,
    commission: Number(document.querySelector("#commission").value) / 100,
    slippage: Number(document.querySelector("#slippage").value) / 100,
  };
}

const percent = new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 2 });
const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

function formatMetric(key, value) {
  if (value === null) return "∞";
  if (["total_return", "annualized_return", "volatility", "max_drawdown", "win_rate"].includes(key)) return percent.format(value);
  return number.format(value);
}

function renderMetrics(result) {
  const labels = {
    total_return: "Total return", annualized_return: "Annualized return", volatility: "Volatility",
    sharpe_ratio: "Sharpe ratio", sortino_ratio: "Sortino ratio", max_drawdown: "Max drawdown",
    win_rate: "Win rate", profit_factor: "Profit factor",
  };
  const root = document.querySelector("#metrics");
  root.replaceChildren();
  Object.entries(labels).forEach(([key, label]) => {
    const card = document.createElement("div");
    const value = result.metrics[key];
    card.className = `metric ${key.includes("return") && value > 0 ? "positive" : ""} ${key === "total_return" && value < 0 ? "negative" : ""}`;
    const caption = document.createElement("span");
    const metricValue = document.createElement("strong");
    caption.textContent = label;
    metricValue.textContent = formatMetric(key, value);
    card.append(caption, metricValue);
    root.append(card);
  });
}

function renderTrades(trades) {
  const root = document.querySelector("#trade-table");
  root.replaceChildren();
  document.querySelector("#trade-count").textContent = `${trades.length} completed`;
  if (!trades.length) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="5" class="empty-row">No completed trades in this period.</td>';
    root.append(row);
    return;
  }
  trades.slice().reverse().slice(0, 25).forEach((trade) => {
    const row = document.createElement("tr");
    const tone = trade.pnl >= 0 ? "gain" : "loss";
    row.innerHTML = `<td>${trade.entry_date}<br><small>@ $${number.format(trade.entry_price)}</small></td>
      <td>${trade.exit_date}<br><small>@ $${number.format(trade.exit_price)}</small></td>
      <td>${number.format(trade.shares)}</td><td class="${tone}">${percent.format(trade.return_pct)}</td>
      <td class="${tone}">${currency.format(trade.pnl)}</td>`;
    root.append(row);
  });
}

function niceRange(values) {
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (min === max) { min -= 1; max += 1; }
  const padding = (max - min) * 0.1;
  return [min - padding, max + padding];
}

function pathFor(values, width, height, padding, min, max) {
  return values.map((value, index) => {
    const x = padding.left + (index / Math.max(values.length - 1, 1)) * (width - padding.left - padding.right);
    const y = padding.top + ((max - value) / (max - min)) * (height - padding.top - padding.bottom);
    return `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");
}

function renderChart(type) {
  if (!latestResult) return;
  activeChart = type;
  document.querySelectorAll("[data-chart]").forEach((button) => {
    const selected = button.dataset.chart === type;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-selected", selected ? "true" : "false");
  });
  const values = latestResult.series[type];
  const dates = latestResult.series.dates;
  const width = 900, height = 290, padding = { left: 66, right: 14, top: 18, bottom: 30 };
  let [min, max] = niceRange(values);
  if (type === "drawdown") max = Math.max(0, max);
  const path = pathFor(values, width, height, padding, min, max);
  const bottom = height - padding.bottom;
  const lastX = width - padding.right;
  const area = `${path} L${lastX},${bottom} L${padding.left},${bottom} Z`;
  const label = { equity: "Portfolio equity", drawdown: "Peak-to-trough drawdown", close: `${latestResult.ticker} adjusted close` }[type];
  document.querySelector("#chart-label").textContent = label;
  document.querySelector("#chart-value").textContent = type === "equity" ? currency.format(values.at(-1)) : type === "drawdown" ? percent.format(values.at(-1)) : `$${number.format(values.at(-1))}`;
  const formatAxis = (value) => type === "drawdown" ? percent.format(value) : type === "equity" ? `$${number.format(value / 1000)}k` : `$${number.format(value)}`;
  const grid = [0, 1, 2, 3].map((step) => {
    const y = padding.top + step / 3 * (height - padding.top - padding.bottom);
    const value = max - step / 3 * (max - min);
    return `<line class="axis-line" x1="${padding.left}" x2="${width - padding.right}" y1="${y}" y2="${y}"/><text class="axis-label" x="0" y="${y + 3}">${formatAxis(value)}</text>`;
  }).join("");
  const dateLabels = [0, Math.floor((dates.length - 1) / 2), dates.length - 1].map((index) => {
    const x = padding.left + index / Math.max(dates.length - 1, 1) * (width - padding.left - padding.right);
    return `<text class="axis-label" x="${x}" y="${height - 5}" text-anchor="${index === 0 ? "start" : index === dates.length - 1 ? "end" : "middle"}">${dates[index]}</text>`;
  }).join("");
  document.querySelector("#chart").innerHTML = `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
    <defs><linearGradient id="area-gradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b8e85c" stop-opacity=".22"/><stop offset="1" stop-color="#b8e85c" stop-opacity="0"/></linearGradient></defs>
    ${grid}${dateLabels}<path class="chart-area" d="${area}"/><path class="chart-line" d="${path}"/>
    <circle class="chart-dot" cx="${lastX}" cy="${padding.top + ((max - values.at(-1)) / (max - min)) * (height - padding.top - padding.bottom)}" r="4"/>
  </svg>`;
}

function renderResult(result) {
  latestResult = result;
  document.querySelector("#result-ticker").textContent = result.ticker;
  document.querySelector("#result-strategy").textContent = strategyLabels[result.strategy];
  document.querySelector("#period-label").innerHTML = `${result.period.start} → ${result.period.end}<br>${number.format(result.period.sessions)} market sessions`;
  renderMetrics(result);
  renderTrades(result.trades);
  renderChart(activeChart);
  showState("results");
  animateResults();
}

function animateResults() {
  if (!window.gsap || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const timeline = window.gsap.timeline({ defaults: { ease: "power3.out" } });
  timeline
    .from(".results-heading", { opacity: 0, y: 20, duration: 0.45 })
    .from(".metric", { opacity: 0, y: 36, scale: 0.94, duration: 0.5, stagger: 0.045 }, "-=0.2")
    .from(".chart-card", { opacity: 0, y: 44, scale: 0.96, duration: 0.6 }, "-=0.25")
    .from(".trades-card", { opacity: 0, y: 42, duration: 0.55 }, "-=0.3");
}

async function runBacktest(event) {
  event.preventDefault();
  runButton.disabled = true;
  document.querySelector("#run-label").textContent = "Running…";
  showState("loading");
  try {
    setApiStatus();
    const response = await fetch("/api/backtest", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(requestPayload()),
    });
    const result = await readJsonResponse(response);
    renderResult(result);
  } catch (error) {
    if (error.message === API_OFFLINE_MESSAGE) setApiStatus(error.message);
    document.querySelector("#error-message").textContent = error.message;
    showState("error");
  } finally {
    runButton.disabled = false;
    document.querySelector("#run-label").textContent = "Run backtest";
  }
}

function resetForm() {
  form.reset();
  document.querySelector("#start").value = "2018-01-01";
  document.querySelector("#end").value = new Date().toISOString().slice(0, 10);
  renderParameters();
  latestResult = null;
  showState("empty");
}

document.querySelector("#end").value = new Date().toISOString().slice(0, 10);
strategySelect.addEventListener("change", renderParameters);
form.addEventListener("submit", runBacktest);
document.querySelector("#reset-button").addEventListener("click", resetForm);
document.querySelector("#dismiss-error").addEventListener("click", () => showState(latestResult ? "results" : "empty"));
document.querySelectorAll("[data-chart]").forEach((button) => button.addEventListener("click", () => renderChart(button.dataset.chart)));
renderParameters();

function initializeMotion() {
  if (
    !window.gsap
    || !window.ScrollTrigger
    || window.matchMedia("(prefers-reduced-motion: reduce)").matches
  ) return;

  window.gsap.registerPlugin(window.ScrollTrigger);
  const gsap = window.gsap;

  gsap.from(".console-hero .eyebrow", { opacity: 0, y: 16, duration: 0.65, ease: "power3.out" });
  gsap.from(".console-hero h1", { opacity: 0, y: 34, duration: 0.9, delay: 0.08, ease: "power3.out" });
  gsap.from(".console-hero-copy > p:not(.eyebrow), .hero-actions", {
    opacity: 0,
    y: 22,
    duration: 0.75,
    delay: 0.23,
    stagger: 0.09,
    ease: "power3.out",
  });
  gsap.to(".console-hero-image", {
    scale: 1.08,
    opacity: 0.55,
    ease: "none",
    scrollTrigger: {
      trigger: ".console-hero",
      start: "top top",
      end: "bottom top",
      scrub: 1,
    },
  });
  gsap.from(".workspace-intro", {
    opacity: 0.15,
    y: 42,
    ease: "none",
    scrollTrigger: {
      trigger: ".workspace-intro",
      start: "top 88%",
      end: "top 52%",
      scrub: 0.8,
    },
  });
  gsap.from(".workspace", {
    opacity: 0.2,
    y: 48,
    scale: 0.96,
    ease: "none",
    scrollTrigger: {
      trigger: ".workspace",
      start: "top 91%",
      end: "top 48%",
      scrub: 1,
    },
  });
  gsap.fromTo(
    ".empty-image-wrap",
    { opacity: 0.25, scale: 0.86 },
    {
      opacity: 1,
      scale: 1,
      ease: "none",
      scrollTrigger: {
        trigger: ".empty-image-wrap",
        start: "top 92%",
        end: "top 55%",
        scrub: 0.8,
      },
    },
  );
}

initializeMotion();
checkApiHealth();
