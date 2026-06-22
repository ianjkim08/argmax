const strategyValues = [
  100000, 99500, 100840, 102100, 101300, 104900, 106400, 105700, 109800, 112200,
  110900, 114500, 118400, 116600, 122100, 125800, 124000, 129600, 133200, 131100,
  136900, 141700, 139400, 145800, 149200, 147900, 153600, 158800, 156400, 162900,
  168100, 165300, 171700, 176400, 173900, 179800, 184720,
];

const benchmarkValues = [
  100000, 97600, 101400, 99800, 104600, 108900, 106800, 112700, 116100, 111300,
  119800, 124700, 121500, 128600, 133900, 130100, 138800, 144200, 137900, 147100,
  152600, 148000, 157900, 165500, 159300, 170800, 177900, 169400, 181300, 190400,
  183100, 196600, 207300, 199700, 215900, 224300, 218100,
];

const dateLabels = ["JAN 2018", "JAN 2019", "JAN 2020", "JAN 2021", "JAN 2022", "JAN 2023", "JAN 2024", "DEC 2025"];
const chartRoot = document.querySelector("#landing-chart");
const chartReadout = document.querySelector("#chart-readout");
const chartDate = document.querySelector("#chart-date");
let visibleSeries = "strategy";

function scalePath(values, width, height, padding, min, max) {
  return values.map((value, index) => {
    const x = padding.left + index / (values.length - 1) * (width - padding.left - padding.right);
    const y = padding.top + (max - value) / (max - min) * (height - padding.top - padding.bottom);
    return `${index ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}

function chartMarkup(hoverIndex = null) {
  const width = 1000;
  const height = 350;
  const padding = { left: 58, right: 16, top: 14, bottom: 29 };
  const min = 85000;
  const max = 235000;
  const strategyPath = scalePath(strategyValues, width, height, padding, min, max);
  const benchmarkPath = scalePath(benchmarkValues, width, height, padding, min, max);
  const horizontalGrid = [100000, 140000, 180000, 220000].map((value) => {
    const y = padding.top + (max - value) / (max - min) * (height - padding.top - padding.bottom);
    return `<line class="landing-grid" x1="${padding.left}" x2="${width - padding.right}" y1="${y}" y2="${y}"/><text class="landing-axis" x="0" y="${y + 3}">$${value / 1000}k</text>`;
  }).join("");
  const dates = dateLabels.map((label, index) => {
    const x = padding.left + index / (dateLabels.length - 1) * (width - padding.left - padding.right);
    const anchor = index === 0 ? "start" : index === dateLabels.length - 1 ? "end" : "middle";
    return `<text class="landing-axis" x="${x}" y="${height - 4}" text-anchor="${anchor}">${label}</text>`;
  }).join("");
  const showStrategy = visibleSeries !== "benchmark";
  const showBenchmark = visibleSeries !== "strategy";
  let hover = "";

  if (hoverIndex !== null) {
    const x = padding.left + hoverIndex / (strategyValues.length - 1) * (width - padding.left - padding.right);
    const dots = [];
    if (showStrategy) {
      const y = padding.top + (max - strategyValues[hoverIndex]) / (max - min) * (height - padding.top - padding.bottom);
      dots.push(`<circle class="hover-dot" stroke="#b8e85c" cx="${x}" cy="${y}" r="4"/>`);
    }
    if (showBenchmark) {
      const y = padding.top + (max - benchmarkValues[hoverIndex]) / (max - min) * (height - padding.top - padding.bottom);
      dots.push(`<circle class="hover-dot" stroke="#8da8ed" cx="${x}" cy="${y}" r="4"/>`);
    }
    hover = `<line class="hover-line" x1="${x}" x2="${x}" y1="${padding.top}" y2="${height - padding.bottom}"/>${dots.join("")}`;
  }

  return `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">${horizontalGrid}${dates}${showBenchmark ? `<path class="benchmark-path" d="${benchmarkPath}"/>` : ""}${showStrategy ? `<path class="strategy-path" d="${strategyPath}"/>` : ""}${hover}</svg>`;
}

function renderChart(index = null) {
  if (chartRoot) chartRoot.innerHTML = chartMarkup(index);
}

document.querySelectorAll("[data-series]").forEach((button) => {
  button.addEventListener("click", () => {
    visibleSeries = button.dataset.series;
    document.querySelectorAll("[data-series]").forEach((item) => {
      const active = item === button;
      item.classList.toggle("active", active);
      item.setAttribute("aria-selected", active ? "true" : "false");
    });
    const values = visibleSeries === "benchmark" ? benchmarkValues : strategyValues;
    chartReadout.textContent = `$${values.at(-1).toLocaleString()}`;
    document.querySelector("#hero-equity").textContent = `$${values.at(-1).toLocaleString()}`;
    document.querySelector("#hero-change").textContent = `+${((values.at(-1) / values[0] - 1) * 100).toFixed(2)}%`;
    renderChart();
  });
});

if (chartRoot) {
  chartRoot.addEventListener("pointermove", (event) => {
    const bounds = chartRoot.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width));
    const index = Math.round(ratio * (strategyValues.length - 1));
    const values = visibleSeries === "benchmark" ? benchmarkValues : strategyValues;
    chartReadout.textContent = `$${values[index].toLocaleString()}`;
    const year = 2018 + index / (strategyValues.length - 1) * 8;
    chartDate.textContent = year.toFixed(1);
    renderChart(index);
  });

  chartRoot.addEventListener("pointerleave", () => {
    const values = visibleSeries === "benchmark" ? benchmarkValues : strategyValues;
    chartReadout.textContent = `$${values.at(-1).toLocaleString()}`;
    chartDate.textContent = "DEC 31, 2025";
    renderChart();
  });
}

async function copyText(value, button) {
  const original = button.querySelector("span")?.textContent || button.textContent;
  try {
    await navigator.clipboard.writeText(value);
    if (button.querySelector("span")) button.querySelector("span").textContent = "Copied";
    else button.textContent = "Copied";
  } catch {
    if (button.querySelector("span")) button.querySelector("span").textContent = "Select";
    else button.textContent = "Select code";
  }
  window.setTimeout(() => {
    if (button.querySelector("span")) button.querySelector("span").textContent = original;
    else button.textContent = original;
  }, 1400);
}

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", () => copyText(button.dataset.copy, button));
});

const copyCodeButton = document.querySelector("#copy-code");
if (copyCodeButton) {
  copyCodeButton.addEventListener("click", () => {
    copyText(document.querySelector("pre code").textContent, copyCodeButton);
  });
}

const methodItems = Array.from(document.querySelectorAll(".method-item"));
function activateMethod(item) {
  methodItems.forEach((candidate) => candidate.classList.toggle("is-active", candidate === item));
}
methodItems.forEach((item) => {
  item.addEventListener("mouseenter", () => activateMethod(item));
  item.addEventListener("focus", () => activateMethod(item));
  item.addEventListener("click", () => activateMethod(item));
});

const evidenceTrack = document.querySelector("#evidence-track");
const evidenceCards = Array.from(document.querySelectorAll("#evidence-track article"));
let evidenceIndex = 0;

function setEvidenceIndex(nextIndex) {
  if (!evidenceTrack || !evidenceCards.length) return;
  evidenceIndex = (nextIndex + evidenceCards.length) % evidenceCards.length;
  const cardWidth = evidenceCards[0].getBoundingClientRect().width;
  evidenceTrack.style.transform = `translate3d(${-evidenceIndex * (cardWidth + 10)}px, 0, 0)`;
}

document.querySelector("#evidence-prev")?.addEventListener("click", () => setEvidenceIndex(evidenceIndex - 1));
document.querySelector("#evidence-next")?.addEventListener("click", () => setEvidenceIndex(evidenceIndex + 1));

function initializeMotion() {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduceMotion || !window.gsap || !window.ScrollTrigger) return;

  window.gsap.registerPlugin(window.ScrollTrigger);
  const gsap = window.gsap;

  gsap.from(".hero-kicker", { opacity: 0, y: 18, duration: .7, ease: "power3.out" });
  gsap.from(".hero-copy h1", { opacity: 0, y: 34, duration: 1, delay: .08, ease: "power3.out" });
  gsap.from(".hero-copy > p:not(.hero-kicker), .hero-actions", { opacity: 0, y: 24, duration: .8, delay: .24, stagger: .1, ease: "power3.out" });
  gsap.from(".execution-card", { opacity: 0, y: 32, scale: .94, duration: .9, delay: .34, ease: "power3.out" });
  gsap.to(".hero-image", {
    scale: 1.06,
    ease: "none",
    scrollTrigger: { trigger: ".hero-section", start: "top top", end: "bottom top", scrub: 1 },
  });

  gsap.from(".research-terminal", {
    opacity: .2,
    scale: .86,
    ease: "none",
    scrollTrigger: { trigger: ".research-terminal", start: "top 88%", end: "top 32%", scrub: 1 },
  });

  gsap.utils.toArray(".capability").forEach((card) => {
    gsap.from(card, {
      opacity: .15,
      scale: .88,
      ease: "none",
      scrollTrigger: { trigger: card, start: "top 92%", end: "top 45%", scrub: .8 },
    });
  });

  const motionMedia = gsap.matchMedia();
  motionMedia.add("(min-width: 1101px)", () => {
    const methodPin = window.ScrollTrigger.create({
      trigger: ".method-section",
      start: "top top",
      end: "bottom bottom",
      pin: ".method-pin",
      pinSpacing: false,
    });
    return () => methodPin.kill();
  });

  const scrubCopy = document.querySelector(".scrub-copy");
  const words = scrubCopy.textContent.trim().split(/\s+/);
  scrubCopy.innerHTML = words.map((word) => `<span class="scrub-word">${word}</span>`).join(" ");
  gsap.to(".scrub-word", {
    opacity: 1,
    stagger: .08,
    ease: "none",
    scrollTrigger: {
      trigger: ".manifesto-section",
      start: "top 70%",
      end: "bottom 55%",
      scrub: 1,
    },
  });

  gsap.utils.toArray(".evidence-track article").forEach((card) => {
    gsap.from(card, {
      opacity: .15,
      scale: .9,
      ease: "none",
      scrollTrigger: { trigger: card, start: "top 90%", end: "top 48%", scrub: .7 },
    });
  });

  gsap.from(".closing-section h2", {
    opacity: .1,
    scale: .88,
    ease: "none",
    scrollTrigger: { trigger: ".closing-section", start: "top 80%", end: "center 55%", scrub: 1 },
  });
}

renderChart();
initializeMotion();
