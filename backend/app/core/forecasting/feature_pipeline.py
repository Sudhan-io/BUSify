import pandas as pd
import numpy as np
from sqlalchemy import text
from backend.app.database import engine

def load_raw_area_demand_dataset() -> pd.DataFrame:
    """
    Loads raw stop-level demand observations joined with stops and calendar,
    then aggregates demand to the (area_id, date) level.
    """
    query = """
    SELECT 
        d.date,
        s.area_id,
        c.day_of_week,
        c.is_holiday,
        c.exam_flag,
        SUM(d.riders) as total_riders
    FROM demand_obs d
    JOIN stops s ON d.stop_id = s.stop_id
    JOIN calendar c ON d.date = c.date
    GROUP BY d.date, s.area_id, c.day_of_week, c.is_holiday, c.exam_flag
    ORDER BY s.area_id, d.date ASC
    """
    df = pd.read_sql(text(query), con=engine)
    df["date"] = pd.to_datetime(df["date"])
    df["is_holiday"] = df["is_holiday"].astype(int)
    df["exam_flag"] = df["exam_flag"].astype(int)
    return df

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs machine learning features for each area time-series:
    - Temporal: day_of_week, is_monday, is_friday, day_of_month
    - Calendar flags: exam_flag, is_holiday
    - Lags: lag_1 (previous operating day), lag_7 (same day prior week)
    - Rolling metrics: rolling_7_mean, rolling_14_mean
    """
    dfs = []
    for area_id, group in df.groupby("area_id"):
        g = group.sort_values("date").copy()
        
        # Temporal indicators
        g["is_monday"] = (g["day_of_week"] == 0).astype(int)
        g["is_friday"] = (g["day_of_week"] == 4).astype(int)
        g["day_of_month"] = g["date"].dt.day
        
        # Lagged demand features
        g["lag_1"] = g["total_riders"].shift(1)
        g["lag_7"] = g["total_riders"].shift(5)  # Approx 1 business week ago
        
        # Rolling window features
        g["rolling_7_mean"] = g["total_riders"].shift(1).rolling(window=5, min_periods=1).mean()
        g["rolling_14_mean"] = g["total_riders"].shift(1).rolling(window=10, min_periods=1).mean()
        
        dfs.append(g)
        
    if not dfs:
        return pd.DataFrame()

    featured_df = pd.concat(dfs, ignore_index=True)

    # Drop rows whose lag/rolling window is not fully determined by prior days.
    # Backfilling these would inject FUTURE observations into the earliest rows,
    # which leaks target information into the training set and produces lag
    # values the model could never see at inference time.
    featured_df = featured_df.dropna(
        subset=["lag_1", "lag_7", "rolling_7_mean", "rolling_14_mean"]
    ).reset_index(drop=True)

    return featured_df


def load_calendar_flags() -> pd.DataFrame:
    """
    Loads the academic calendar as a date-indexed lookup of (is_holiday, exam_flag).

    Unlike `load_raw_area_demand_dataset`, this covers calendar dates that have no
    demand observations yet (e.g. the forecast horizon), so the inference path can
    resolve holiday flags instead of assuming every future day is a working day.
    """
    query = """
    SELECT date, is_holiday, exam_flag
    FROM calendar
    ORDER BY date ASC
    """
    df = pd.read_sql(text(query), con=engine)
    df["date"] = pd.to_datetime(df["date"])
    return df
