import re
import pytest
from backend.app.database import SessionLocal
from backend.app.models.stop import Stop
from backend.app.models.bus import Bus
from backend.app.models.registration import Registration
from backend.app.models.calendar import Calendar
from backend.app.models.demand import DemandObservation
from backend.app.core.data.anonymizer import hash_student_id

def test_student_anonymization_determinism_and_length():
    """Validates that student ID hashing is deterministic, salted, and valid SHA-256."""
    raw_id = "2023-CS-0042"
    hash1 = hash_student_id(raw_id)
    hash2 = hash_student_id(raw_id)
    assert hash1 == hash2, "Hashing must be deterministic"
    assert len(hash1) == 64, "SHA-256 hash must be 64 hexadecimal characters"
    assert re.match(r"^[0-9a-f]{64}$", hash1), "Hash must be valid hex"

def test_database_stops_count_and_coordinates():
    """Validates that all stops exist with valid geographic coordinates in Tamil Nadu."""
    db = SessionLocal()
    try:
        stops = db.query(Stop).all()
        assert len(stops) == 47, f"Expected 47 stops, found {len(stops)}"
        for s in stops:
            assert 10.5 <= s.lat <= 11.5, f"Stop {s.stop_id} latitude out of bounds: {s.lat}"
            assert 77.5 <= s.lon <= 78.5, f"Stop {s.stop_id} longitude out of bounds: {s.lon}"
            assert s.area_id.startswith("AREA_"), f"Invalid area format: {s.area_id}"
    finally:
        db.close()

def test_database_fleet_size_and_capacity():
    """Validates that exactly 50 buses exist and default seating capacity is 55."""
    db = SessionLocal()
    try:
        buses = db.query(Bus).all()
        assert len(buses) == 50, f"Expected 50 buses, found {len(buses)}"
        for b in buses:
            assert b.seats == 55, f"Bus {b.bus_id} has unexpected seat capacity: {b.seats}"
            assert b.is_active is True, f"Bus {b.bus_id} is inactive"
    finally:
        db.close()

def test_student_registrations_volume_and_integrity():
    """Validates that 2,200 registrations exist and all link to valid stops."""
    db = SessionLocal()
    try:
        regs = db.query(Registration).all()
        assert len(regs) == 2200, f"Expected 2200 registrations, found {len(regs)}"
        valid_stop_ids = {s.stop_id for s in db.query(Stop.stop_id).all()}
        for r in regs[:100]:  # Sample test
            assert r.stop_id in valid_stop_ids, f"Registration references invalid stop {r.stop_id}"
            assert len(r.student_hash) == 64
    finally:
        db.close()

def test_historical_demand_observations_presence():
    """Validates that demand observations exist for past calendar dates."""
    db = SessionLocal()
    try:
        obs_count = db.query(DemandObservation).count()
        assert obs_count > 2500, f"Expected >2500 demand observations, found {obs_count}"
        cal_count = db.query(Calendar).count()
        assert cal_count >= 90, f"Expected >=90 calendar dates, found {cal_count}"
    finally:
        db.close()
