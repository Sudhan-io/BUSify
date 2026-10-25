"""
lightgbm_model.py — Quantile demand forecaster (p50 / p90) per geographic area.

Two separate paths exist and must stay consistent:

  TRAINING   — `build_features` derives lag/rolling columns from each area's
               observed series, then rows with an undefined window are dropped.
  INFERENCE  — `_lag_features` reconstructs the *same* columns for an arbitrary
               target date from the observations that precede it.

The offsets below are the single source of truth for both paths. Changing one
without the other reintroduces train/inference feature skew.
"""

from __future__ import annotations

import logging
import threading

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

from backend.app.core.forecasting.feature_pipeline import (
    load_raw_area_demand_dataset,
    load_calendar_flags,
    build_features,
)
from backend.app.core.forecasting.baseline import (
    SameWeekdayBaseline,
    calculate_wape,
    calculate_rmse,
)

logger = logging.getLogger(__name__)

FEATURE_COLS = [
    "area_encoded",
    "day_of_week",
    "is_monday",
    "is_friday",
    "day_of_month",
    "is_holiday",
    "exam_flag",
    "lag_1",
    "lag_7",
    "rolling_7_mean",
    "rolling_14_mean",
]

# Window sizes mirroring feature_pipeline.build_features. The inference path
# rebuilds features with these exact offsets.
LAG_WEEKLY_OFFSET = 5      # "lag_7" is 5 operating days back (not 7 calendar days)
ROLLING_SHORT_WINDOW = 5   # "rolling_7_mean"
ROLLING_LONG_WINDOW = 10   # "rolling_14_mean"


class DemandForecastModel:
    """
    Quantile regression model trained with LightGBM to produce
    median (p50) and peak (p90) ridership predictions per geographic area.

    Dataset state (raw aggregate, engineered features, per-area history and the
    calendar lookup) is loaded once and cached in memory. Call `invalidate_cache`
    after seeding or loading new observations.
    """

    def __init__(self):
        self.encoder = LabelEncoder()
        self.model_p50 = None
        self.model_p90 = None
        self.baseline_model = SameWeekdayBaseline()
        self.metrics = {}
        self._train_lock = threading.Lock()
        self._raw_df = None
        self._feature_df = None
        self._area_history = None
        self._calendar_lookup = None

    # ── cached dataset access ───────────────────────────────────────────────
    def invalidate_cache(self) -> None:
        """Drops every cached dataset artefact. Call after re-seeding or bulk loading."""
        with self._train_lock:
            self._raw_df = None
            self._feature_df = None
            self._area_history = None
            self._calendar_lookup = None

    def _raw_dataset(self, refresh: bool = False) -> pd.DataFrame:
        if self._raw_df is None or refresh:
            self._raw_df = load_raw_area_demand_dataset()
            self._feature_df = None
            self._area_history = None
        return self._raw_df

    def prepare_data(self, refresh: bool = False) -> pd.DataFrame:
        """Loads and feature-engineers the dataset, caching the result."""
        raw_df = self._raw_dataset(refresh=refresh)
        if self._feature_df is None:
            self._feature_df = build_features(raw_df)
        return self._feature_df

    def _area_series(self, refresh: bool = False) -> dict:
        """Maps area_id -> (ascending date array, ascending rider array)."""
        self._raw_dataset(refresh=refresh)
        if self._area_history is None:
            history = {}
            for area_id, group in self._raw_df.groupby("area_id"):
                ordered = group.sort_values("date")
                history[area_id] = (
                    ordered["date"].to_numpy(),
                    ordered["total_riders"].astype(float).to_numpy(),
                )
            self._area_history = history
        return self._area_history

    def _calendar(self, refresh: bool = False) -> dict:
        """Maps a normalised Timestamp -> (is_holiday, exam_flag)."""
        if self._calendar_lookup is None or refresh:
            try:
                flags = load_calendar_flags()
                self._calendar_lookup = {
                    row.date: (int(row.is_holiday), int(row.exam_flag))
                    for row in flags.itertuples()
                }
            except Exception:
                logger.warning(
                    "Calendar lookup unavailable; holiday/exam flags will fall back "
                    "to the weekday heuristic for all dates.",
                    exc_info=True,
                )
                self._calendar_lookup = {}
        return self._calendar_lookup

    # ── training ────────────────────────────────────────────────────────────
    def train_and_evaluate(self, test_days: int = 14) -> dict:
        """
        Trains LightGBM models with a temporal split (last `test_days` days held
        out) and records accuracy against the same-weekday baseline.
        """
        df = self.prepare_data(refresh=True).copy()
        if df.empty:
            raise RuntimeError(
                "Cannot train demand forecaster: no rows have a fully determined "
                "lag/rolling window. Check that demand_obs and calendar are seeded."
            )

        # Fit the encoder once, here. prepare_data() is called on every prediction
        # and must never re-fit it, or previously encoded labels become invalid.
        df["area_encoded"] = self.encoder.fit_transform(df["area_id"])

        split_date = df["date"].max() - pd.Timedelta(days=test_days)
        train_df = df[df["date"] < split_date].copy()
        test_df = df[df["date"] >= split_date].copy()

        if train_df.empty or test_df.empty:
            raise RuntimeError(
                "Temporal train/test split produced an empty partition "
                f"(train={len(train_df)}, test={len(test_df)}). "
                "Increase history depth or reduce test_days."
            )

        X_train = train_df[FEATURE_COLS]
        y_train = train_df["total_riders"]
        X_test = test_df[FEATURE_COLS]
        y_test = test_df["total_riders"]

        self.baseline_model.fit(train_df)
        baseline_preds = self.baseline_model.predict(test_df)
        baseline_wape = calculate_wape(y_test.values, baseline_preds)
        baseline_rmse = calculate_rmse(y_test.values, baseline_preds)

        self.model_p50 = lgb.LGBMRegressor(
            objective="quantile",
            alpha=0.50,
            n_estimators=100,
            learning_rate=0.05,
            num_leaves=15,
            random_state=42,
            verbosity=-1,
        )
        self.model_p50.fit(X_train, y_train)

        self.model_p90 = lgb.LGBMRegressor(
            objective="quantile",
            alpha=0.90,
            n_estimators=100,
            learning_rate=0.05,
            num_leaves=15,
            random_state=42,
            verbosity=-1,
        )
        self.model_p90.fit(X_train, y_train)

        lgbm_p50_preds = self.model_p50.predict(X_test)
        lgbm_p90_preds = self.model_p90.predict(X_test)

        lgbm_wape = calculate_wape(y_test.values, lgbm_p50_preds)
        lgbm_rmse = calculate_rmse(y_test.values, lgbm_p50_preds)

        self.metrics = {
            "baseline_wape": round(baseline_wape, 4),
            "baseline_rmse": round(baseline_rmse, 2),
            "lightgbm_p50_wape": round(lgbm_wape, 4),
            "lightgbm_p50_rmse": round(lgbm_rmse, 2),
            "wape_improvement_pct": (
                round(((baseline_wape - lgbm_wape) / baseline_wape) * 100, 2)
                if baseline_wape > 0
                else None
            ),
            "p90_mean": round(float(np.mean(lgbm_p90_preds)), 2),
            "test_sample_count": len(test_df),
        }

        return self.metrics

    def _ensure_trained(self) -> None:
        """Lazily trains the models. Safe against concurrent first requests."""
        if self.model_p50 is not None and self.model_p90 is not None:
            return
        with self._train_lock:
            if self.model_p50 is not None and self.model_p90 is not None:
                return
            logger.info("Demand forecaster cold start — training p50/p90 models.")
            self.train_and_evaluate()

    # ── inference ───────────────────────────────────────────────────────────
    def _lag_features(self, target_dt: pd.Timestamp, area_id: str) -> dict | None:
        """
        Rebuilds lag/rolling features for `target_dt` from the observations that
        precede it, using the same offsets as `build_features`.

        Returns None when the area has no observation on or before the target
        date, i.e. the feature vector would be undefined.
        """
        history = self._area_series()
        entry = history.get(area_id)
        if entry is None:
            return None

        dates, riders = entry
        # First observation strictly after the target date; the row we are
        # synthesising would sit at this index, so the latest usable observation
        # is one position earlier.
        target_np = np.datetime64(target_dt)
        next_index = int(np.searchsorted(dates, target_np, side="left"))
        last = next_index - 1
        if last < 0:
            return None

        def at(offset: int) -> float:
            position = last - offset
            return float(riders[position]) if position >= 0 else float(riders[0])

        short_start = max(0, last - ROLLING_SHORT_WINDOW + 1)
        long_start = max(0, last - ROLLING_LONG_WINDOW + 1)

        return {
            "lag_1": at(0),
            "lag_7": at(LAG_WEEKLY_OFFSET - 1),
            "rolling_7_mean": float(riders[short_start:last + 1].mean()),
            "rolling_14_mean": float(riders[long_start:last + 1].mean()),
        }

    def _is_holiday(self, target_dt: pd.Timestamp) -> int:
        """Holiday flag for the target date, defaulting to the weekday rule."""
        flags = self._calendar().get(target_dt)
        if flags is not None:
            return flags[0]
        # The seeder marks weekends as holidays; mirror that beyond the calendar
        # horizon instead of assuming every future day is a working day.
        return 1 if target_dt.weekday() >= 5 else 0

    def predict_for_date(
        self, target_date_str: str, area_id: str, exam_flag: bool = False
    ) -> dict:
        """
        Generates p50 and p90 demand predictions for a target date and area.

        Raises:
            ValueError: if the area is unknown or has no usable history before
                the target date. Callers must validate `area_id` first.
        """
        self._ensure_trained()

        try:
            target_dt = pd.to_datetime(target_date_str)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid target date '{target_date_str}'; expected YYYY-MM-DD."
            ) from exc
        if pd.isna(target_dt):
            raise ValueError(
                f"Invalid target date '{target_date_str}'; expected YYYY-MM-DD."
            )

        if area_id not in self.encoder.classes_:
            raise ValueError(
                f"Unknown area_id '{area_id}'. The forecaster was trained on: "
                f"{sorted(self.encoder.classes_)}."
            )

        lag_features = self._lag_features(target_dt, area_id)
        if lag_features is None:
            raise ValueError(
                f"No demand observations on or before {target_date_str} for area "
                f"'{area_id}'; lag features are undefined."
            )

        dow = target_dt.weekday()
        row_dict = {
            "area_encoded": [float(self.encoder.transform([area_id])[0])],
            "day_of_week": [dow],
            "is_monday": [1 if dow == 0 else 0],
            "is_friday": [1 if dow == 4 else 0],
            "day_of_month": [target_dt.day],
            "is_holiday": [self._is_holiday(target_dt)],
            "exam_flag": [1 if exam_flag else 0],
            "lag_1": [lag_features["lag_1"]],
            "lag_7": [lag_features["lag_7"]],
            "rolling_7_mean": [lag_features["rolling_7_mean"]],
            "rolling_14_mean": [lag_features["rolling_14_mean"]],
        }
        X_infer = pd.DataFrame(row_dict)[FEATURE_COLS]

        p50 = float(self.model_p50.predict(X_infer)[0])
        p90 = float(self.model_p90.predict(X_infer)[0])

        # Enforce physical monotonicity: p90 >= p50
        p90 = max(p90, p50 * 1.05)

        return {
            "area_id": area_id,
            "date": target_date_str,
            "p50_demand": int(round(p50)),
            "p90_demand": int(round(p90)),
        }


# Global singleton
forecaster = DemandForecastModel()