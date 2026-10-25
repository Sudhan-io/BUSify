from ortools.sat.python import cp_model
from backend.app.config import settings

class FleetAllocationOptimizer:
    """
    Solves optimal bus fleet distribution across geographic zones using OR-Tools CP-SAT.
    Minimizes standing students (p90 demand), excess empty seats, and operational churn.
    """
    def __init__(self, total_fleet: int = None, bus_capacity: int = None):
        self.total_fleet = total_fleet or settings.TOTAL_FLEET_SIZE
        self.bus_capacity = bus_capacity or settings.DEFAULT_BUS_CAPACITY
        self.w_standing = settings.WEIGHT_STANDING_PENALTY
        self.w_empty = settings.WEIGHT_EMPTY_SEAT_PENALTY
        self.w_churn = settings.WEIGHT_CHURN_PENALTY

    def solve(
        self,
        predicted_demands: dict[str, int],
        current_allocations: dict[str, int] = None,
        min_coverage: dict[str, int] = None
    ) -> dict:
        """
        Solves the Integer Program:
        Args:
            predicted_demands: Mapping of area_id -> p90 predicted riders (e.g., {'AREA_A': 390, 'AREA_B': 620})
            current_allocations: Mapping of area_id -> baseline bus count (e.g., {'AREA_A': 10, 'AREA_B': 12})
            min_coverage: Mapping of area_id -> minimum buses required (e.g., {'AREA_A': 2})
        Returns:
            Dictionary with optimal allocation, metrics, and slack values.
        """
        areas = list(predicted_demands.keys())
        model = cp_model.CpModel()

        # Decision variables
        n = {}  # Bus count per area
        s = {}  # Standing students slack
        e = {}  # Empty seats slack
        d = {}  # Churn slack |n_a - current_a|

        for a in areas:
            # Capacity bounded between min coverage and total fleet
            min_buses = min_coverage.get(a, 2) if min_coverage else 2
            n[a] = model.NewIntVar(min_buses, self.total_fleet, f"buses_{a}")
            
            # Demand upper bound for slack domain
            d_val = predicted_demands[a]
            max_cap = self.total_fleet * self.bus_capacity
            
            s[a] = model.NewIntVar(0, max(d_val, 1000), f"standing_{a}")
            e[a] = model.NewIntVar(0, max_cap, f"empty_{a}")
            d[a] = model.NewIntVar(0, self.total_fleet, f"churn_{a}")

            # Standing constraint: s_a >= D_a - (C * n_a)
            # s_a + C * n_a >= D_a
            model.Add(s[a] + self.bus_capacity * n[a] >= d_val)

            # Empty seats constraint: e_a >= (C * n_a) - D_a
            # e_a - C * n_a >= -D_a
            model.Add(e[a] - self.bus_capacity * n[a] >= -d_val)

            # Churn constraints: d_a >= |n_a - n_current,a|
            cur_val = current_allocations.get(a, self.total_fleet // len(areas)) if current_allocations else (self.total_fleet // len(areas))
            model.Add(d[a] >= n[a] - cur_val)
            model.Add(d[a] >= cur_val - n[a])

        # Global fleet constraint: sum(n_a) <= total_fleet
        model.Add(sum(n[a] for a in areas) <= self.total_fleet)

        # Objective Function
        objective_terms = []
        for a in areas:
            objective_terms.append(self.w_standing * s[a])
            objective_terms.append(self.w_empty * e[a])
            objective_terms.append(self.w_churn * d[a])
            
        model.Minimize(sum(objective_terms))

        # Solve model
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        status = solver.Solve(model)

        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            raise RuntimeError(f"CP-SAT solver failed to find feasible solution. Status code: {status}")

        optimized_allocation = {a: solver.Value(n[a]) for a in areas}
        standing_per_area = {a: solver.Value(s[a]) for a in areas}
        empty_per_area = {a: solver.Value(e[a]) for a in areas}
        churn_per_area = {a: solver.Value(d[a]) for a in areas}

        total_buses_used = sum(optimized_allocation.values())
        total_standing = sum(standing_per_area.values())
        total_empty = sum(empty_per_area.values())
        total_churn = sum(churn_per_area.values())

        return {
            "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
            "total_fleet_available": self.total_fleet,
            "total_buses_allocated": total_buses_used,
            "allocation": optimized_allocation,
            "metrics": {
                "total_predicted_standing_students": total_standing,
                "total_empty_seats": total_empty,
                "total_fleet_churn_adjustments": total_churn,
            },
            "per_area_details": {
                a: {
                    "allocated_buses": optimized_allocation[a],
                    "total_seat_capacity": optimized_allocation[a] * self.bus_capacity,
                    "predicted_demand_p90": predicted_demands[a],
                    "standing_students": standing_per_area[a],
                    "empty_seats": empty_per_area[a],
                    "churn_from_baseline": churn_per_area[a],
                }
                for a in areas
            }
        }

fleet_allocator = FleetAllocationOptimizer()
