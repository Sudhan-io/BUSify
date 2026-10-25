import numpy as np
import pandas as pd

def calculate_wape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Calculates Weighted Absolute Percentage Error (WAPE)."""
    total_actual = np.sum(actual)
    if total_actual == 0:
        return 0.0
    return float(np.sum(np.abs(actual - predicted)) / total_actual)

def calculate_rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Calculates Root Mean Squared Error (RMSE)."""
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))

class SameWeekdayBaseline:
    """
    Baseline model that predicts demand using the average of previous
    observations for the same day-of-week within the same area.
    """
    def __init__(self):
        self.history = {}

    def fit(self, train_df: pd.DataFrame):
        """Fits historical mean lookup table: (area_id, day_of_week) -> mean riders."""
        self.history = (
            train_df.groupby(["area_id", "day_of_week"])["total_riders"]
            .mean()
            .to_dict()
        )
        self.overall_area_mean = (
            train_df.groupby("area_id")["total_riders"]
            .mean()
            .to_dict()
        )

    def predict(self, test_df: pd.DataFrame) -> np.ndarray:
        """Predicts expected demand for given test records."""
        predictions = []
        for _, row in test_df.iterrows():
            key = (row["area_id"], row["day_of_week"])
            val = self.history.get(key, self.overall_area_mean.get(row["area_id"], 150.0))
            predictions.append(val)
        return np.array(predictions)
