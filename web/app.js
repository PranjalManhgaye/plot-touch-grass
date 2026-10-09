const form = document.getElementById("check-form");
const presetButtons = document.getElementById("preset-buttons");
const engineStatus = document.getElementById("engine-status");
const submitBtn = document.getElementById("submit-btn");
const resultEl = document.getElementById("result");

const fields = [
  "lat",
  "lon",
  "avg_temp_c",
  "min_temp_c",
  "precip_mm",
  "wind_kmh",
  "soil_moisture",
  "days_since_last_frost",
];

function setFields(data) {
  for (const key of fields) {
    if (data[key] !== undefined && data[key] !== null) {
      document.getElementById(key).value = data[key];
    }
  }
}

function readForm() {
  const payload = {};
  for (const key of fields) {
    payload[key] = Number(document.getElementById(key).value);
  }
  return payload;
}

async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (!data.ready) {
      engineStatus.textContent = data.error || "Model failed to load.";
      engineStatus.className = "engine-line warn";
      return;
    }
    if (data.loading) {
      engineStatus.textContent = "Engine: loading TabPFN…";
      engineStatus.className = "engine-line warn";
    } else if (data.engine === "tabpfn") {
      engineStatus.textContent = `Engine: TabPFN · ${data.training_rows.toLocaleString()} training rows`;
      engineStatus.className = "engine-line ok";
    } else if (data.engine === "baseline") {
      engineStatus.textContent =
        "Engine: local baseline (set TABPFN_TOKEN for real TabPFN)";
      engineStatus.className = "engine-line warn";
    } else {
      engineStatus.textContent = "Engine: starting…";
      engineStatus.className = "engine-line warn";
    }
  } catch {
    engineStatus.textContent = "Could not reach the API.";
    engineStatus.className = "engine-line warn";
  }
}

async function loadPresets() {
  const res = await fetch("/api/presets");
  const presets = await res.json();
  presetButtons.innerHTML = "";
  presets.forEach((preset, index) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "preset" + (index === 0 ? " active" : "");
    btn.textContent = preset.label;
    btn.title = preset.region;
    btn.addEventListener("click", () => {
      document.querySelectorAll(".preset").forEach((el) => el.classList.remove("active"));
      btn.classList.add("active");
      setFields(preset);
    });
    presetButtons.appendChild(btn);
  });
}

function renderResult(data) {
  resultEl.hidden = false;
  document.getElementById("result-kicker").textContent =
    data.action.toUpperCase() + " · " + Math.round(data.confidence * 100) + "% confidence";
  document.getElementById("result-title").textContent = data.verdict.title;
  document.getElementById("result-sub").textContent = data.verdict.subtitle;

  const conf = document.getElementById("confidence");
  conf.innerHTML = "";
  const order = ["wait", "walk", "garden"];
  for (const key of order) {
    if (data.probabilities[key] === undefined) continue;
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.innerHTML = `${key} <strong>${Math.round(data.probabilities[key] * 100)}%</strong>`;
    conf.appendChild(chip);
  }

  const list = document.getElementById("checklist");
  list.innerHTML = "";
  for (const item of data.checklist) {
    const li = document.createElement("li");
    li.innerHTML = `
      <span class="step">${item.step}</span>
      <div>
        <h4>${item.title}</h4>
        <p>${item.detail}</p>
      </div>
    `;
    list.appendChild(li);
  }

  document.getElementById("model-note").textContent =
    data.engine === "tabpfn"
      ? `Predicted by ${data.model_note}.`
      : data.model_note;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitBtn.disabled = true;
  submitBtn.textContent = "Reading the table…";
  try {
    const res = await fetch("/api/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(readForm()),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Request failed");
    }
    const data = await res.json();
    renderResult(data);
    resultEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (err) {
    engineStatus.textContent = err.message || "Something went wrong.";
    engineStatus.className = "engine-line warn";
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Get outdoor signal";
  }
});

loadHealth();
loadPresets();
