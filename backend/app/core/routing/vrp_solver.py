from datetime import datetime, timedelta
import math

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from backend.app.config import settings
from backend.app.core.routing.matrix_service import matrix_service
from backend.app.core.routing.road_geometry_service import road_geometry_service


def _haversine_route_km(itinerary: list[dict]) -> float:
    """
    Computes the actual cumulative Haversine route distance in km
    from an ordered itinerary list of {lat, lon} dicts.
    Used in the heuristic fallback to replace fabricated distance arithmetic.
    """
    R = 6371.0
    total_km = 0.0
    coords = [(s["lat"], s["lon"]) for s in itinerary if "lat" in s and "lon" in s]
    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        total_km += R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # Apply road detour index: straight-line understimates real road distance
    return round(total_km * settings.ROAD_DETOUR_INDEX, 2)


class CapacitatedVRPSolver:
    """
    Solves the Capacitated Vehicle Routing Problem (CVRP) for a single area.
    Assigns stops and generates ordered routes for all available buses in the zone.
    Includes automated split-pickup preprocessing for high-density transit stops.
    """
    def __init__(self, bus_capacity: int = None):
        self.bus_capacity = bus_capacity or settings.DEFAULT_BUS_CAPACITY

    def _preprocess_stops(self, stops: list[dict], num_buses: int = 6) -> list[dict]:
        """
        Partitions stops with demand exceeding target pickup chunk size into
        multiple virtual pickup visits at the exact same location.
        Ensures nodes can be combinatorially packed into available vehicle bins.
        """
        processed_stops = []
        # Target chunk size allows multiple stops to be served per vehicle without violating capacity
        target_chunk_size = min(30, int(self.bus_capacity * 0.60))

        for s in stops:
            demand = int(s.get("p90_riders", 10))
            if demand <= target_chunk_size:
                processed_stops.append(dict(s))
            else:
                part = 1
                while demand > 0:
                    current_chunk = min(demand, target_chunk_size)
                    virtual_stop = dict(s)
                    virtual_stop["stop_id"] = f"{s['stop_id']}_P{part}"
                    virtual_stop["name"] = f"{s['name']} (Batch {part})"
                    virtual_stop["p90_riders"] = current_chunk
                    virtual_stop["is_split"] = True
                    processed_stops.append(virtual_stop)
                    demand -= current_chunk
                    part += 1

        return processed_stops

    def solve(
        self,
        area_id: str,
        stops: list[dict],
        num_buses: int,
        college_depot: tuple[float, float] = None,
        target_arrival_time: str = "08:30",
        include_road_geometry: bool = True,
        direction: str = "MORNING_PICKUP"
    ) -> dict:
        """
        Solves CVRP with split delivery support.
        """
        if num_buses <= 0:
            return {"status": "ERROR", "message": "At least one bus must be allocated.", "routes": []}

        depot_coords = college_depot or (settings.COLLEGE_DEPOT_LAT, settings.COLLEGE_DEPOT_LON)

        # Preprocess high-density stops to ensure single node demand <= bus capacity
        sanitized_stops = self._preprocess_stops(stops, num_buses)

        # Build full coordinate list: index 0 is depot, 1..N are stops
        all_coords = [depot_coords] + [(s["lat"], s["lon"]) for s in sanitized_stops]
        num_nodes = len(all_coords)

        # Demands: 0 at depot, stop demand at indices 1..N
        demands = [0] + [int(s.get("p90_riders", 10)) for s in sanitized_stops]

        # Calculate distance and duration matrices
        dist_matrix, dur_matrix = matrix_service.get_matrices(all_coords)

        # Create routing index manager: N nodes, num_buses vehicles, depot at 0
        manager = pywrapcp.RoutingIndexManager(num_nodes, num_buses, 0)
        routing = pywrapcp.RoutingModel(manager)

        # Distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return dist_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Capacity dimension
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            [self.bus_capacity] * num_buses,  # vehicle capacities
            True,  # start cumul to zero
            "Capacity"
        )

        # Search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )
        search_parameters.time_limit.seconds = 2

        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            # Fallback heuristic: Capacity-constrained bin packing
            return self._heuristic_fallback_routes(area_id, sanitized_stops, num_buses, depot_coords, target_arrival_time, include_road_geometry)

        # Parse solution routes
        routes = []
        target_dt = datetime.strptime(target_arrival_time, "%H:%M")

        for vehicle_id in range(num_buses):
            index = routing.Start(vehicle_id)
            route_dist_meters = 0
            route_dur_seconds = 0
            route_load = 0

            # Follow vehicle path
            node_sequence = []
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                node_sequence.append(node)
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_dist_meters += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                to_node = manager.IndexToNode(index)
                route_dur_seconds += dur_matrix[node][to_node]

            # Add depot return node
            node_sequence.append(0)

            # Skip empty unused buses
            visited_stops_indices = [idx for idx in node_sequence if idx != 0]
            if not visited_stops_indices:
                continue

            # Backward-scheduled arrival times, floored at the earliest
            # permissible departure. Segment durations are real OSRM values, so
            # an unterminated subtraction chain could run past midnight.
            earliest_dt = datetime.strptime(
                settings.EARLIEST_ROUTE_DEPARTURE, "%H:%M"
            )
            current_time = target_dt
            schedule_feasible = True
            scheduled_steps = []

            for i in range(len(node_sequence) - 1, -1, -1):
                curr_node = node_sequence[i]
                if i > 0:
                    prev_node = node_sequence[i - 1]
                    segment_duration = dur_matrix[prev_node][curr_node]
                else:
                    segment_duration = 0

                if current_time < earliest_dt:
                    current_time = earliest_dt
                    schedule_feasible = False

                time_str = current_time.strftime("%H:%M")

                if curr_node == 0 and i == len(node_sequence) - 1:
                    scheduled_steps.append({
                        "node_type": "depot_arrival",
                        "name": settings.COLLEGE_NAME,
                        "time": time_str,
                        "lat": depot_coords[0],
                        "lon": depot_coords[1],
                        "boarded": 0,
                    })
                elif curr_node != 0:
                    stop_obj = sanitized_stops[curr_node - 1]
                    boarded = demands[curr_node]
                    route_load += boarded
                    scheduled_steps.append({
                        "node_type": "pickup_stop",
                        "stop_id": stop_obj["stop_id"],
                        "name": stop_obj["name"],
                        "time": time_str,
                        "lat": stop_obj["lat"],
                        "lon": stop_obj["lon"],
                        "boarded": boarded,
                    })
                elif curr_node == 0 and i == 0:
                    scheduled_steps.append({
                        "node_type": "depot_departure",
                        "name": f"{settings.COLLEGE_NAME} (Depot Out)",
                        "time": time_str,
                        "lat": depot_coords[0],
                        "lon": depot_coords[1],
                        "boarded": 0,
                    })

                current_time -= timedelta(seconds=segment_duration)

            scheduled_steps.reverse()

            if direction == "EVENING_DROP":
                # For evening drop: departs campus hub at 16:30 and drops outward
                start_dt = datetime.strptime("16:30", "%H:%M")
                evening_steps = []
                cur_dt = start_dt
                # Start at Campus Hub
                evening_steps.append({
                    "node_type": "depot_departure",
                    "name": f"{settings.COLLEGE_NAME} (Campus Dismissal)",
                    "time": cur_dt.strftime("%H:%M"),
                    "lat": depot_coords[0],
                    "lon": depot_coords[1],
                    "boarded": 0,
                    "disembarked": 0
                })
                # Reverse stops order so inner stops are reached first
                pickup_nodes = [s for s in scheduled_steps if s.get("node_type") == "pickup_stop"]
                pickup_nodes.reverse()
                for p_idx, p_node in enumerate(pickup_nodes):
                    cur_dt += timedelta(minutes=int(5 + p_idx * 3))
                    evening_steps.append({
                        "node_type": "dropoff_stop",
                        "stop_id": p_node.get("stop_id"),
                        "name": p_node.get("name"),
                        "time": cur_dt.strftime("%H:%M"),
                        "lat": p_node.get("lat"),
                        "lon": p_node.get("lon"),
                        "boarded": 0,
                        "disembarked": p_node.get("boarded", 5)
                    })
                # Final terminal
                cur_dt += timedelta(minutes=8)
                evening_steps.append({
                    "node_type": "depot_arrival",
                    "name": "Corridor Outer Terminal Depot",
                    "time": cur_dt.strftime("%H:%M"),
                    "lat": evening_steps[-1]["lat"] if len(evening_steps) > 1 else depot_coords[0],
                    "lon": evening_steps[-1]["lon"] if len(evening_steps) > 1 else depot_coords[1],
                    "boarded": 0,
                    "disembarked": 0
                })
                scheduled_steps = evening_steps

            waypoints = [(step["lat"], step["lon"]) for step in scheduled_steps if "lat" in step and "lon" in step]
            if include_road_geometry:
                road_coords = road_geometry_service.get_road_geometry(waypoints)
            else:
                road_coords = [[lat, lon] for lat, lon in waypoints]

            dur_mins = round(route_dur_seconds / 60.0, 1)

            routes.append({
                "bus_index": vehicle_id + 1,
                "bus_code": f"BUS-AREA_{area_id[-1]}-{vehicle_id + 1:02d}",
                "capacity": self.bus_capacity,
                "total_riders": route_load,
                "utilization_pct": round((route_load / self.bus_capacity) * 100, 1),
                "total_distance_km": round(route_dist_meters / 1000.0, 2),
                "total_duration_minutes": dur_mins,
                "direction": direction,
                "commute_comfort_certified": dur_mins <= 60.0,
                "schedule_feasible": schedule_feasible,
                "max_travel_time_cap": 60,
                "stop_count": len(visited_stops_indices),
                "itinerary": scheduled_steps,
                "road_geometry": road_coords,
            })

        return {
            "status": "SUCCESS",
            "area_id": area_id,
            "buses_utilized": len(routes),
            "buses_allocated": num_buses,
            "total_riders_served": sum(r["total_riders"] for r in routes),
            "total_distance_km": round(sum(r["total_distance_km"] for r in routes), 2),
            "routes": routes
        }

    def _heuristic_fallback_routes(
        self,
        area_id: str,
        stops: list[dict],
        num_buses: int,
        depot_coords: tuple,
        target_arrival_time: str,
        include_road_geometry: bool = True
    ) -> dict:
        """
        Capacity-constrained First-Fit-Decreasing bin packing fallback.
        Strictly guarantees no bus exceeds seating capacity.
        """
        routes = []
        buses_chunks = [[] for _ in range(num_buses)]
        bus_loads = [0] * num_buses

        # Sort stops descending by demand for optimal bin packing
        sorted_stops = sorted(stops, key=lambda s: s.get("p90_riders", 10), reverse=True)

        for s in sorted_stops:
            rem = s.get("p90_riders", 10)
            for b_idx in range(num_buses):
                if rem <= 0:
                    break
                avail = self.bus_capacity - bus_loads[b_idx]
                if avail > 0:
                    take = min(rem, avail)
                    chunk = dict(s)
                    chunk["p90_riders"] = take
                    buses_chunks[b_idx].append(chunk)
                    bus_loads[b_idx] += take
                    rem -= take

        for b_idx, chunk in enumerate(buses_chunks):
            if not chunk:
                continue
            total_load = bus_loads[b_idx]

            # Schedule pickups by walking forward from the earliest permissible
            # departure. The previous f"08:{5 + i * 5:02d}" arithmetic emitted
            # invalid times such as "08:65" for routes with 12+ stops.
            pickup_clock = datetime.strptime(
                settings.EARLIEST_ROUTE_DEPARTURE, "%H:%M"
            ) + timedelta(minutes=settings.FALLBACK_DEPOT_DWELL_MINUTES)
            pickup_steps = []
            for s in chunk:
                pickup_steps.append({
                    "node_type": "pickup_stop",
                    "stop_id": s["stop_id"],
                    "name": s["name"],
                    "time": pickup_clock.strftime("%H:%M"),
                    "lat": s["lat"],
                    "lon": s["lon"],
                    "boarded": s["p90_riders"],
                })
                pickup_clock += timedelta(minutes=settings.FALLBACK_STOP_DWELL_MINUTES)

            itinerary = [
                {"node_type": "depot_departure", "name": f"{settings.COLLEGE_NAME} (Depot Out)", "time": datetime.strptime(settings.EARLIEST_ROUTE_DEPARTURE, "%H:%M").strftime("%H:%M"), "lat": depot_coords[0], "lon": depot_coords[1], "boarded": 0}
            ] + pickup_steps + [
                {"node_type": "depot_arrival", "name": settings.COLLEGE_NAME, "time": target_arrival_time, "lat": depot_coords[0], "lon": depot_coords[1], "boarded": 0}
            ]
            waypoints = [(step["lat"], step["lon"]) for step in itinerary if "lat" in step and "lon" in step]
            if include_road_geometry:
                road_coords = road_geometry_service.get_road_geometry(waypoints)
            else:
                road_coords = [[lat, lon] for lat, lon in waypoints]

            routes.append({
                "bus_index": b_idx + 1,
                "bus_code": f"BUS-AREA_{area_id[-1]}-{b_idx + 1:02d}",
                "capacity": self.bus_capacity,
                "total_riders": total_load,
                "utilization_pct": round((total_load / self.bus_capacity) * 100, 1),
                "total_distance_km": _haversine_route_km(itinerary),
                "total_duration_minutes": round(_haversine_route_km(itinerary) / settings.AVERAGE_BUS_SPEED_KMH * 60, 1),
                "stop_count": len(chunk),
                "itinerary": itinerary,
                "road_geometry": road_coords,
            })

        return {
            "status": "SUCCESS",
            "area_id": area_id,
            "buses_utilized": len(routes),
            "buses_allocated": num_buses,
            "total_riders_served": sum(r["total_riders"] for r in routes),
            "total_distance_km": round(sum(r["total_distance_km"] for r in routes), 2),
            "routes": routes
        }

vrp_solver = CapacitatedVRPSolver()
