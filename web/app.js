const form = document.getElementById("check-form");
const presetButtons = document.getElementById("preset-buttons");
const engineStatus = document.getElementById("engine-status");
const weatherSource = document.getElementById("weather-source");
const submitBtn = document.getElementById("submit-btn");
const geoBtn = document.getElementById("geo-btn");
const refreshBtn = document.getElementById("refresh-weather-btn");
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

let activePreset = null;

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

async function loadWeather(lat, lon, label) {
  weatherSource.textContent = "Fetching live weather from Open-Meteo…";
  weatherSource.className = "weather-source";
  refreshBtn.disabled = true;
  geoBtn.disabled = true;
  try {
    const res = await fetch(`/api/weather?lat=${lat}&lon=${lon}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Weather fetch failed");
    }
    const data = await res.json();
    setFields(data);
    const place = label || `${lat.toFixed(2)}, ${lon.toFixed(2)}`;
    weatherSource.textContent = `${place} · ${data.source} · heuristic hint: ${data.suggested_action}`;
    weatherSource.className = "weather-source ok";
    return data;
  } catch (err) {
    weatherSource.textContent = err.message || "Could not load weather.";
    weatherSource.className = "weather-source";
    throw err;
  } finally {
    refreshBtn.disabled = false;
    geoBtn.disabled = false;
  }
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
    const rows = data.training_rows?.toLocaleString() ?? "?";
    const src = data.data_source ? ` · ${data.data_source}` : "";
    if (data.loading) {
      engineStatus.textContent = "Engine: loading TabPFN…";
      engineStatus.className = "engine-line warn";
    } else if (data.engine === "tabpfn") {
      engineStatus.textContent = `Engine: TabPFN · ${rows} real weather rows${src}`;
      engineStatus.className = "engine-line ok";
    } else if (data.engine === "baseline") {
      engineStatus.textContent = "Engine: local baseline (set TABPFN_TOKEN for real TabPFN)";
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
    btn.addEventListener("click", async () => {
      document.querySelectorAll(".preset").forEach((el) => el.classList.remove("active"));
      btn.classList.add("active");
      activePreset = preset;
      document.getElementById("lat").value = preset.lat;
      document.getElementById("lon").value = preset.lon;
      await loadWeather(preset.lat, preset.lon, preset.label);
    });
    presetButtons.appendChild(btn);
  });
  if (presets[0]) {
    activePreset = presets[0];
    await loadWeather(presets[0].lat, presets[0].lon, presets[0].label);
  }
}

function renderResult(data) {
  resultEl.hidden = false;
  document.getElementById("result-kicker").textContent =
    data.action.toUpperCase() + " · " + Math.round(data.confidence * 100) + "% confidence";
  document.getElementById("result-title").textContent = data.verdict.title;
  document.getElementById("result-sub").textContent = data.verdict.subtitle;

  const conf = document.getElementById("confidence");
  conf.innerHTML = "";
  for (const key of ["wait", "walk", "garden"]) {
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

geoBtn.addEventListener("click", () => {
  if (!navigator.geolocation) {
    weatherSource.textContent = "Geolocation not supported in this browser.";
    return;
  }
  geoBtn.disabled = true;
  weatherSource.textContent = "Getting your location…";
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      document.querySelectorAll(".preset").forEach((el) => el.classList.remove("active"));
      activePreset = null;
      const { latitude, longitude } = pos.coords;
      document.getElementById("lat").value = latitude;
      document.getElementById("lon").value = longitude;
      try {
        await loadWeather(latitude, longitude, "Your location");
      } catch {
        /* loadWeather sets message */
      }
    },
    () => {
      weatherSource.textContent = "Location permission denied.";
      geoBtn.disabled = false;
    },
    { enableHighAccuracy: false, timeout: 15000 }
  );
});

refreshBtn.addEventListener("click", async () => {
  const lat = Number(document.getElementById("lat").value);
  const lon = Number(document.getElementById("lon").value);
  const label = activePreset?.label ?? "Selected coordinates";
  await loadWeather(lat, lon, label);
});

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
