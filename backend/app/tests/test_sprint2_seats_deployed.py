import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.bus import Bus

client = TestClient(app)

def test_seats_deployed_sums_mixed_capacities():
    """Verify that buses with different seat capacities are summed accurately (DATA-002)."""
    with SessionLocal() as db:
        # Initial baseline: 50 buses * 55 seats = 2750
        bus1 = db.query(Bus).filter(Bus.bus_id == "BUS-01").first()
        bus2 = db.query(Bus).filter(Bus.bus_id == "BUS-02").first()
        orig_seats1 = bus1.seats
        orig_seats2 = bus2.seats

        try:
            # Change BUS-01 to 30 seats (minibus) and BUS-02 to 42 seats
            bus1.seats = 30
            bus2.seats = 42
            db.commit()

            res = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
            assert res.status_code == 200
            data = res.json()

            expected_seats = (50 * 55) - (55 - 30) - (55 - 42)  # 2750 - 25 - 13 = 2712
            assert data["total_seats_deployed"] == expected_seats
        finally:
            bus1.seats = orig_seats1
            bus2.seats = orig_seats2
            db.commit()

def test_seats_deployed_excludes_inactive_buses():
    """Verify that inactive buses do not contribute to total_seats_deployed."""
    with SessionLocal() as db:
        bus1 = db.query(Bus).filter(Bus.bus_id == "BUS-01").first()
        bus2 = db.query(Bus).filter(Bus.bus_id == "BUS-02").first()
        orig_active1 = bus1.is_active
        orig_active2 = bus2.is_active

        try:
            # Deactivate 2 buses
            bus1.is_active = False
            bus2.is_active = False
            db.commit()

            res = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
            assert res.status_code == 200
            data = res.json()

            expected_seats = 48 * 55  # 2640
            assert data["total_seats_deployed"] == expected_seats
        finally:
            bus1.is_active = orig_active1
            bus2.is_active = orig_active2
            db.commit()

def test_seats_deployed_empty_active_fleet():
    """Verify that an empty active fleet returns zero seats deployed and 0.0% utilization."""
    with SessionLocal() as db:
        # Save active status of all buses
        buses = db.query(Bus).all()
        status_map = {b.bus_id: b.is_active for b in buses}

        try:
            # Set all buses inactive
            db.query(Bus).update({Bus.is_active: False})
            db.commit()

            res = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
            assert res.status_code == 200
            data = res.json()

            assert data["total_seats_deployed"] == 0
            assert data["overall_utilization_pct"] == 0.0
        finally:
            for b in buses:
                b.is_active = status_map[b.bus_id]
            db.commit()

def test_seats_deployed_independent_of_manifest_length():
    """Verify that manifest entry count does not dictate total_seats_deployed."""
    res = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
    assert res.status_code == 200
    data = res.json()

    manifest_len = len(data["manifest"])
    # In regular scenario, manifest has ~38 entries, while total active fleet has 50 buses (2750 seats)
    assert manifest_len != 50
    assert data["total_seats_deployed"] == 2750
    # Must NOT equal the old flawed formula: len(manifest) * capacity
    assert data["total_seats_deployed"] != manifest_len * data["bus_capacity"]

def test_seats_deployed_contract_compatibility():
    """Verify that all existing operational manifest response fields remain present and compatible."""
    res = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
    assert res.status_code == 200
    data = res.json()

    required_keys = [
        "date",
        "scenario",
        "surge_multiplier",
        "bus_capacity",
        "total_active_buses",
        "total_seats_deployed",
        "total_expected_riders",
        "overall_utilization_pct",
        "total_standing",
        "total_empty",
        "churn",
        "manifest",
        "area_allocation",
        "baseline_allocation",
    ]
    for key in required_keys:
        assert key in data, f"Missing required response key: {key}"

    assert isinstance(data["total_seats_deployed"], int)
    assert isinstance(data["overall_utilization_pct"], float)
    assert data["total_seats_deployed"] > 0
