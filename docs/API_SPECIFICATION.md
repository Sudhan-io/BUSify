# BUSify: REST API Specification

This document details the complete REST API interface exposed by the BUSify backend platform running at default base URL `http://localhost:8000/api`.

---

## Interactive Documentation
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`

---

## 1. System Metadata & Health

### `GET /`
Returns system operational metadata.
* **Response `200 OK`**:
```json
{
  "platform": "BUSify Transit Optimization Platform",
  "version": "0.2.0",
  "docs_url": "/docs",
  "api_prefix": "/api",
  "status": "OPERATIONAL"
}
```

### `GET /api/health`
Verifies backend runtime health, database connectivity, and fleet parameters.
* **Response `200 OK`**:
```json
{
  "status": "HEALTHY",
  "database_connected": true,
  "total_fleet_size": 50,
  "bus_capacity": 55,
  "target_arrival_time": "08:30",
  "college_hub": "Central Engineering College Transit Hub"
}
```

---

## 2. Transit Network & Fleet Catalog

### `GET /api/stops`
Lists all designated campus bus stops with geographic coordinates and zone groupings.
* **Response `200 OK`**:
```json
[
  {
    "stop_id": "ST-A01",
    "name": "Central Bus Stand",
    "lat": 10.9575,
    "lon": 78.0815,
    "area_id": "AREA_A",
    "sequence_order": 1
  }
]
```

### `GET /api/buses`
Lists the college-owned vehicle fleet specifications.
* **Response `200 OK`**:
```json
[
  {
    "bus_id": "BUS-01",
    "seats": 55,
    "default_area_id": "AREA_A",
    "is_active": true
  }
]
```

---

## 3. Demand Forecasting Engine

### `GET /api/forecast`
Generates quantile demand predictions ($p50$ median and $p90$ peak headroom) for all 5 zones.
* **Query Parameters:**
  - `date` *(string, optional)*: Target forecast date (`YYYY-MM-DD`). Defaults to current date.
* **Response `200 OK`**:
```json
{
  "date": "2026-10-15",
  "is_exam_day": false,
  "areas": [
    {
      "area_id": "AREA_A",
      "date": "2026-10-15",
      "p50_demand": 380,
      "p90_demand": 410
    }
  ],
  "total_p50_demand": 1620,
  "total_p90_demand": 1850
}
```

---

## 4. Macro Fleet Optimization

### `GET /api/allocation`
Solves OR-Tools CP-SAT integer program distributing 50 buses across regional zones.
* **Query Parameters:**
  - `date` *(string, optional)*: Date for optimization (`YYYY-MM-DD`).
* **Response `200 OK`**:
```json
{
  "date": "2026-10-15",
  "status": "OPTIMAL",
  "total_fleet_available": 50,
  "total_buses_allocated": 50,
  "baseline_allocation": { "AREA_A": 10, "AREA_B": 12, "AREA_C": 8, "AREA_D": 12, "AREA_E": 8 },
  "optimized_allocation": { "AREA_A": 9, "AREA_B": 13, "AREA_C": 8, "AREA_D": 12, "AREA_E": 8 },
  "metrics": {
    "total_predicted_standing_students": 0,
    "total_empty_seats": 120,
    "total_fleet_churn_adjustments": 2
  },
  "per_area_details": {
    "AREA_B": {
      "allocated_buses": 13,
      "total_seat_capacity": 715,
      "predicted_demand_p90": 690,
      "standing_students": 0,
      "empty_seats": 25,
      "churn_from_baseline": 1
    }
  }
}
```

---

## 5. Micro Capacitated Routing

### `GET /api/routes`
Solves Capacitated Vehicle Routing Problem (CVRP) for the selected zone with reverse arrival scheduling.
* **Query Parameters:**
  - `area_id` *(string, required)*: Zone ID (`AREA_A` to `AREA_E`).
  - `date` *(string, optional)*: Date for route plan (`YYYY-MM-DD`).
* **Response `200 OK`**:
```json
{
  "status": "SUCCESS",
  "area_id": "AREA_A",
  "buses_utilized": 8,
  "buses_allocated": 8,
  "total_riders_served": 408,
  "total_distance_km": 166.4,
  "routes": [
    {
      "bus_index": 1,
      "bus_code": "BUS-AREA_A-01",
      "capacity": 55,
      "total_riders": 55,
      "utilization_pct": 100.0,
      "total_distance_km": 14.5,
      "total_duration_minutes": 28.0,
      "stop_count": 2,
      "itinerary": [
        {
          "node_type": "depot_departure",
          "name": "Central Engineering College Transit Hub (Depot Out)",
          "time": "07:45",
          "lat": 10.9601,
          "lon": 78.0766,
          "boarded": 0
        },
        {
          "node_type": "pickup_stop",
          "stop_id": "ST-A01",
          "name": "Central Bus Stand",
          "time": "08:10",
          "lat": 10.9575,
          "lon": 78.0815,
          "boarded": 30
        },
        {
          "node_type": "depot_arrival",
          "name": "Central Engineering College Transit Hub",
          "time": "08:30",
          "lat": 10.9601,
          "lon": 78.0766,
          "boarded": 0
        }
      ]
    }
  ]
}
```
* **Error Response `400 Bad Request`**:
```json
{ "detail": "Invalid area_id 'INVALID_ZONE'. Available: ['AREA_A', 'AREA_B', 'AREA_C', 'AREA_D', 'AREA_E']" }
```

---

## 6. Student Commuter Crowding Advisory

### `GET /api/crowding`
Returns real-time and predicted congestion indicators for a specific transit vehicle.
* **Query Parameters:**
  - `bus_id` *(string, required)*: Target bus ID (`BUS-01` to `BUS-50`).
  - `date` *(string, optional)*: Date for crowd query (`YYYY-MM-DD`).
* **Response `200 OK`**:
```json
{
  "bus_id": "BUS-02",
  "date": "2026-10-15",
  "seats_capacity": 55,
  "assigned_area_id": "AREA_A",
  "area_name": "Central & Vengamedu",
  "crowd_level": "MODERATE",
  "crowd_badge_color": "amber",
  "utilization_pct": 82.5,
  "expected_riders_p50": 41,
  "expected_riders_p90": 45,
  "advisory_message": "Normal ridership. Most seats will be occupied."
}
```
* **Error Response `404 Not Found`**:
```json
{ "detail": "Bus 'BUS-999' not found in fleet." }
```

---

## 7. Backtesting Simulator

### `POST /api/simulate`
Replays real historical days to benchmark static status quo vs. BUSify demand-aware allocation.
* **Request Body:**
```json
{ "sample_days": 7 }
```
* **Response `200 OK`**:
```json
{
  "status": "SUCCESS",
  "simulated_days_count": 7,
  "summary_kpis": {
    "total_students_transported": 13090,
    "baseline_total_standing_students": 142,
    "dynamic_total_standing_students": 0,
    "standing_students_reduction_pct": 100.0,
    "baseline_overcrowded_trips_pct": 8.6,
    "dynamic_overcrowded_trips_pct": 0.0,
    "service_equity_score_gain": 85.0,
    "total_trips_analyzed": 350
  },
  "daily_records": [...]
}
```

---

## 8. College & Student Operational Workflows

### `GET /api/workflow/operational-manifest`
Generates the actionable Transport Office Fleet Dispatch Manifest.
* **Query Parameters:**
  - `date` *(string, optional)*: Target operational date (`YYYY-MM-DD`).
  - `scenario` *(string, optional)*: Academic timetable scenario (`REGULAR`, `EXAM_DAY`, `PLACEMENT_DRIVE`, `MONSOON_RAIN`).
* **Response `200 OK`**:
```json
{
  "date": "2026-10-15",
  "scenario": "EXAM_DAY",
  "total_active_buses": 47,
  "total_seats_deployed": 2585,
  "total_expected_riders": 2414,
  "overall_utilization_pct": 93.4,
  "manifest": [
    {
      "bus_code": "BUS-01",
      "area_id": "AREA_A",
      "area_name": "Central & Vengamedu",
      "driver_name": "R. Murugan",
      "driver_phone": "+91 90000 00001",
      "capacity": 55,
      "allocated_riders": 52,
      "utilization_pct": 94.5,
      "departure_time": "07:35 AM",
      "campus_arrival": "08:30 AM",
      "total_distance_km": 24.1,
      "stop_count": 5,
      "stops_list": ["Central Stand", "Vengamedu North", "Kovai Road Arch"],
      "status": "APPROVED_DISPATCHED"
    }
  ]
}
```

### `GET /api/workflow/student-profile`
Retrieves verified student commuter transit profile, digital boarding pass, guaranteed seat number, and emergency driver contact.
* **Query Parameters:**
  - `roll_no` *(string, required)*: Student university roll number (e.g. `21CS104`, `22ME045`).
  - `date` *(string, optional)*: Travel date (`YYYY-MM-DD`).
* **Response `200 OK`**:
```json
{
  "student_roll": "21CS104",
  "student_hash": "A92F4D183B7E",
  "academic_year": "2025-2026",
  "assigned_stop": {
    "stop_id": "ST-A02",
    "name": "Vengamedu Junction",
    "area_id": "AREA_A",
    "campus_distance_km": 8.9
  },
  "assigned_bus_code": "BUS-14",
  "driver_name": "M. Velusamy",
  "driver_phone": "+91 90000 00004",
  "seat_number": "Seat #38",
  "seat_guarantee": "CONFIRMED_NO_STANDING",
  "pickup_time": "08:02 AM",
  "campus_arrival": "08:30 AM",
  "traveling_today": true,
  "occupancy_pct": 78,
  "crowd_level": "MODERATE"
}
```

### `POST /api/workflow/student-opt-out`
Real-time student attendance action toggling whether the student is commuting on today's morning bus.
* **Request Body:**
```json
{
  "student_roll": "21CS104",
  "traveling_today": false
}
```
* **Response `200 OK`**:
```json
{
  "student_roll": "21CS104",
  "traveling_today": false,
  "message": "Absence recorded for 21CS104. Seat successfully released for peers.",
  "total_active_opt_outs": 1
}
```

---

## 7. Institutions & Multi-Campus Scalability

### `GET /api/institutions`
Lists all registered college and university campuses.
* **Response `200 OK`**: Array of registered institutions.

### `POST /api/institutions`
Registers a new campus depot. Requires Transport Officer authentication bearer token.
* **Request Body:**
```json
{
  "name": "Thiagarajar College of Engineering",
  "short_name": "TCE Madurai",
  "city": "Madurai",
  "campus_lat": 9.8826,
  "campus_lng": 78.0818,
  "fleet_size": 10,
  "bus_capacity": 55
}
```

### `GET /api/institutions/active`
Returns the currently active institution anchoring transit planning.

### `POST /api/institutions/active`
Switches the globally active campus. Requires Transport Officer authentication bearer token.

---

## 8. Dispatch Plan Approval & Workflow Persistence

### `POST /api/workflow/plan/approve`
Approves and persists the daily dispatch plan atomically to the `plans` table. Requires Transport Officer authentication.
* **Request Body:**
```json
{
  "date": "2026-10-28",
  "scenario": "REGULAR"
}
```
* **Response `200 OK`**:
```json
{
  "status": "SUCCESS",
  "date": "2026-10-28",
  "scenario": "REGULAR",
  "total_buses_dispatched": 16,
  "total_riders_scheduled": 880,
  "message": "Daily dispatch plan approved and persisted to database."
}
```

### `GET /api/workflow/plan/status`
Checks whether an approved dispatch plan is persisted in the database for the given date and scenario.

### `GET /api/buses/drivers`
Lists the complete roster of active bus drivers with assigned vehicles and emergency phone contacts.
