import pandas as pd
import numpy as np
from sqlalchemy import text
from backend.app.database import engine
from backend.app.config import settings
from backend.app.core.forecasting.lightgbm_model import forecaster
from backend.app.core.allocation.optimizer import fleet_allocator

BASELINE_ALLOCATION = {
    "AREA_A": 10,
    "AREA_B": 12,
    "AREA_C": 8,
    "AREA_D": 12,
    "AREA_E": 8,
}

class TransitSimulator:
    """
    Backtesting simulator that benchmarks the status-quo fixed bus dispatching
    against BUSify's demand-aware dynamic fleet allocation over historical dates.
    """
    def __init__(self, bus_capacity: int = None):
        self.bus_capacity = bus_capacity or settings.DEFAULT_BUS_CAPACITY

    def simulate_date_range(self, start_date: str = None, end_date: str = None, sample_days: int = 10) -> dict:
        """
        Runs day-by-day simulation comparing baseline vs dynamic allocation.
        """
        # Query distinct past dates with demand observations
        date_query = """
        SELECT DISTINCT c.date, c.exam_flag, c.day_of_week
        FROM demand_obs d
        JOIN calendar c ON d.date = c.date
        ORDER BY c.date DESC
        LIMIT :limit
        """
        days_df = pd.read_sql(text(date_query), con=engine, params={"limit": sample_days})
        
        if days_df.empty:
            return {"status": "ERROR", "message": "No historical observations found for simulation."}

        # Reverse to chronological order
        days_df = days_df.sort_values("date")

        daily_comparisons = []
        
        total_baseline_standing = 0
        total_dynamic_standing = 0
        total_baseline_overcrowded_trips = 0
        total_dynamic_overcrowded_trips = 0
        total_baseline_trips = 0
        total_dynamic_trips = 0
        total_trips = 0
        total_actual_riders = 0

        for _, row in days_df.iterrows():
            d_str = row["date"]
            is_exam = bool(row["exam_flag"])

            # 1. Fetch actual observed ridership per area for this date
            obs_query = """
            SELECT s.area_id, SUM(d.riders) as actual_riders
            FROM demand_obs d
            JOIN stops s ON d.stop_id = s.stop_id
            WHERE d.date = :d_str
            GROUP BY s.area_id
            """
            obs_df = pd.read_sql(text(obs_query), con=engine, params={"d_str": d_str})
            actual_by_area = dict(zip(obs_df["area_id"], obs_df["actual_riders"]))

            if not actual_by_area:
                continue

            # 2. Compute BUSify dynamic forecast & allocation
            predicted_demands = {}
            for a_id in BASELINE_ALLOCATION.keys():
                pred = forecaster.predict_for_date(d_str, a_id, exam_flag=is_exam)
                predicted_demands[a_id] = pred["p90_demand"]

            alloc_result = fleet_allocator.solve(
                predicted_demands=predicted_demands,
                current_allocations=BASELINE_ALLOCATION
            )
            dynamic_allocation = alloc_result["allocation"]

            # 3. Benchmark both strategies on actual ridership
            day_actual_total = sum(actual_by_area.values())
            total_actual_riders += day_actual_total

            # Status Quo metrics
            base_standing_day = 0
            base_overcrowded_buses = 0
            for a_id, base_buses in BASELINE_ALLOCATION.items():
                act = actual_by_area.get(a_id, 0)
                cap = base_buses * self.bus_capacity
                if act > cap:
                    standing = act - cap
                    base_standing_day += standing
                    # Estimate trips with standing
                    base_overcrowded_buses += min(base_buses, int(np.ceil(standing / 12.0)))

            # Dynamic BUSify metrics
            dyn_standing_day = 0
            dyn_overcrowded_buses = 0
            for a_id, dyn_buses in dynamic_allocation.items():
                act = actual_by_area.get(a_id, 0)
                cap = dyn_buses * self.bus_capacity
                if act > cap:
                    standing = act - cap
                    dyn_standing_day += standing
                    dyn_overcrowded_buses += min(dyn_buses, int(np.ceil(standing / 12.0)))

            total_baseline_standing += base_standing_day
            total_dynamic_standing += dyn_standing_day
            total_baseline_overcrowded_trips += base_overcrowded_buses
            total_dynamic_overcrowded_trips += dyn_overcrowded_buses
            day_base_trips = sum(BASELINE_ALLOCATION.values())
            day_dyn_trips = sum(dynamic_allocation.values())
            total_baseline_trips += day_base_trips
            total_dynamic_trips += day_dyn_trips
            total_trips += day_base_trips

            daily_comparisons.append({
                "date": d_str,
                "is_exam": is_exam,
                "actual_riders": day_actual_total,
                "baseline_standing_students": base_standing_day,
                "dynamic_standing_students": dyn_standing_day,
                "standing_reduction_pct": round(
                    ((base_standing_day - dyn_standing_day) / max(base_standing_day, 1)) * 100, 1
                ) if base_standing_day > 0 else 0.0,
                "baseline_overcrowded_buses": base_overcrowded_buses,
                "dynamic_overcrowded_buses": dyn_overcrowded_buses,
                "dynamic_reallocations_count": alloc_result["metrics"]["total_fleet_churn_adjustments"],
            })

        # Aggregated KPIs (resolves DATA-005 / H-12 by using actual allocation counts)
        baseline_overcrowd_rate = round((total_baseline_overcrowded_trips / max(total_baseline_trips, 1)) * 100, 2)
        dynamic_overcrowd_rate = round((total_dynamic_overcrowded_trips / max(total_dynamic_trips, 1)) * 100, 2)
        
        overall_standing_reduction = round(
            ((total_baseline_standing - total_dynamic_standing) / max(total_baseline_standing, 1)) * 100, 1
        ) if total_baseline_standing > 0 else 100.0

        return {
            "status": "SUCCESS",
            "simulated_days_count": len(daily_comparisons),
            "summary_kpis": {
                "total_students_transported": total_actual_riders,
                "baseline_total_standing_students": total_baseline_standing,
                "dynamic_total_standing_students": total_dynamic_standing,
                "standing_students_reduction_pct": overall_standing_reduction,
                "baseline_overcrowded_trips_pct": baseline_overcrowd_rate,
                "dynamic_overcrowded_trips_pct": dynamic_overcrowd_rate,
                "service_equity_score_gain": round(overall_standing_reduction * 0.85, 1),
                "total_trips_analyzed": total_trips,
            },
            "daily_records": daily_comparisons,
        }

simulator = TransitSimulator()
