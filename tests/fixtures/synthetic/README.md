# Synthetic Test Fixtures Suite for BUSify Route Optimization

This directory contains deterministic, reproducible synthetic fixtures for testing the route optimization pipeline offline.
It is isolated from production databases, credentials, and live external APIs (like OSRM or OpenStreetMap).

---

## Directory Structure

```
tests/fixtures/synthetic/
├── README.md                          # Architecture, schema, and usage guide
├── generate_fixtures.py               # Deterministic fixture generator script
├── expected_results.json              # Canonical baseline expectations for each scenario
├── scenarios/
│   ├── 01_corridor_linear_5stops.json         # Standard linear highway corridor
│   ├── 02_corridor_asymmetric_costs.json      # Asymmetric travel durations (one-way / congestion)
│   ├── 03_oversized_stop_split.json           # Demand > bus capacity (virtual node splitting)
│   ├── 04_infeasible_tight_windows.json       # Infeasible schedule / distant perimeter stops
│   └── 05_duplicate_and_invalid_stops.json    # Edge cases: duplicate coordinates, zero/negative demand
```

---

## JSON Schema Specification

Each scenario file adheres to the following JSON schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SyntheticRoutingScenario",
  "type": "object",
  "required": ["scenario_id", "description", "depot", "bus_capacity", "num_buses", "target_arrival_time", "stops"],
  "properties": {
    "scenario_id": { "type": "string" },
    "description": { "type": "string" },
    "bus_capacity": { "type": "integer", "minimum": 1 },
    "num_buses": { "type": "integer", "minimum": 1 },
    "target_arrival_time": { "type": "string", "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$" },
    "depot": {
      "type": "object",
      "required": ["name", "lat", "lon"],
      "properties": {
        "name": { "type": "string" },
        "lat": { "type": "number" },
        "lon": { "type": "number" }
      }
    },
    "duration_matrix": {
      "description": "Optional asymmetric or custom second-based duration matrix [[depot, s1, s2...]]",
      "type": "array",
      "items": { "type": "array", "items": { "type": "integer" } }
    },
    "stops": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["stop_id", "name", "lat", "lon", "p90_riders"],
        "properties": {
          "stop_id": { "type": "string" },
          "name": { "type": "string" },
          "lat": { "type": "number" },
          "lon": { "type": "number" },
          "sequence_order": { "type": "integer" },
          "p90_riders": { "type": "integer" }
        }
      }
    }
  }
}
```

---

## Scenario Catalog

| ID | File | Key Characteristics | Validated Expectations |
|---|---|---|---|
| **SC-01** | `01_corridor_linear_5stops.json` | 5 stops along NH-81 in increasing distance, demands 15-40 pax. | Routes preserve corridor order; max load $\le$ 55; pickup times are monotonic. |
| **SC-02** | `02_corridor_asymmetric_costs.json` | 6 stops with custom asymmetric duration matrix (forward vs reverse difference). | Solver correctly schedules without assuming Euclidean symmetry. |
| **SC-03** | `03_oversized_stop_split.json` | Stop with demand = 115 (> 2x bus capacity of 50). | Stop preprocessor creates virtual sub-stops $\le 50$; no bus exceeds capacity. |
| **SC-04** | `04_infeasible_tight_windows.json` | Stops 95 km away with target arrival 06:15 (violating 06:00 earliest departure floor). | `schedule_feasible` flag correctly marks `False`; fallback clamps to departure floor safely. |
| **SC-05** | `05_duplicate_and_invalid_stops.json` | Identical lat/lon coordinates, 0-demand stops, negative demand. | Sanitizer removes negative/zero demands and deduplicates nodes safely. |

---

## Generation & Execution

### Regenerate Fixtures
```bash
python tests/fixtures/synthetic/generate_fixtures.py
```

### Run Synthetic Suite
```bash
pytest backend/app/tests/test_synthetic_suite.py -v
```
