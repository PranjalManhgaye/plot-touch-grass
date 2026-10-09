"""TabPFN outdoor-action classifier.

Uses Prior Labs TabPFN (hosted client) when TABPFN_TOKEN is set.
Falls back to a transparent sklearn baseline only for local UI testing —
never presented as TabPFN.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

FEATURE_COLS = [
    "lat",
    "lon",
    "day_of_year",
    "avg_temp_c",
    "min_temp_c",
    "precip_mm",
    "daylight_h",
    "wind_kmh",
    "soil_moisture",
    "days_since_last_frost",
]

LABEL_COL = "action"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "outdoor_history.csv"
DATA_SOURCE = (
    "Open-Meteo ERA5 reanalysis (2018–2024), "
    "12 US cities — labels from documented frost/garden heuristics"
)


@dataclass
class Prediction:
    action: str
    confidence: float
    probabilities: dict[str, float]
    engine: str
    model_note: str


class OutdoorEngine:
    def __init__(self) -> None:
        self.engine = "uninitialized"
        self.model_note = ""
        self._model: Any = None
        self._label_encoder = LabelEncoder()
        self._df: pd.DataFrame | None = None
        self.ready = False
        self.loading = False
        self.error: str | None = None

    def load(self) -> None:
        if self.ready or self.loading:
            return
        self.loading = True
        try:
            self._load_inner()
        finally:
            self.loading = False

    def ensure_ready(self) -> None:
        if not self.ready:
            self.load()

    def _load_inner(self) -> None:
        if not DATA_PATH.exists():
            self.error = f"Missing training data at {DATA_PATH}"
            return

        df = pd.read_csv(DATA_PATH)
        self._df = df
        X = df[FEATURE_COLS]
        y = self._label_encoder.fit_transform(df[LABEL_COL])

        token = os.getenv("TABPFN_TOKEN", "").strip()
        if token:
            try:
                from tabpfn_client import TabPFNClassifier

                # Modest stratified fit — fast enough for free-tier cold starts.
                train_size = min(400, max(60, len(X) - 50))
                X_fit, _, y_fit, _ = train_test_split(
                    X, y, train_size=train_size, stratify=y, random_state=42
                )
                model = TabPFNClassifier()
                model.fit(X_fit, y_fit)
                self._model = model
                self.engine = "tabpfn"
                self.model_note = "Prior Labs TabPFN (hosted client)"
                self.ready = True
                self.error = None
                return
            except Exception as exc:  # noqa: BLE001 — surface setup issues clearly
                self.error = f"TabPFN client failed: {exc}"
                # continue to baseline so the UI still loads for development

        # Transparent baseline — never claimed as TabPFN in API responses
        model = HistGradientBoostingClassifier(max_depth=4, random_state=42)
        model.fit(X, y)
        self._model = model
        self.engine = "baseline"
        self.model_note = (
            "Local HistGradientBoosting baseline. "
            "Set TABPFN_TOKEN to run real TabPFN for the challenge demo."
        )
        self.ready = True

    def predict(self, features: dict[str, float]) -> Prediction:
        self.ensure_ready()
        if not self.ready or self._model is None:
            raise RuntimeError(self.error or "Model not ready")

        row = pd.DataFrame([{c: features[c] for c in FEATURE_COLS}])
        proba = self._model.predict_proba(row)[0]
        classes = self._label_encoder.classes_
        idx = int(np.argmax(proba))
        action = str(classes[idx])
        probabilities = {str(c): float(p) for c, p in zip(classes, proba)}
        return Prediction(
            action=action,
            confidence=float(proba[idx]),
            probabilities=probabilities,
            engine=self.engine,
            model_note=self.model_note,
        )

    def stats(self) -> dict[str, Any]:
        n = 0 if self._df is None else len(self._df)
        return {
            "ready": self.ready,
            "loading": self.loading,
            "engine": self.engine,
            "model_note": self.model_note,
            "training_rows": n,
            "classes": list(self._label_encoder.classes_) if self.ready else [],
            "error": self.error,
            "tabpfn_token_set": bool(os.getenv("TABPFN_TOKEN", "").strip()),
            "data_source": DATA_SOURCE,
        }


engine = OutdoorEngine()
