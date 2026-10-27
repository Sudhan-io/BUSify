import sys
import json
import subprocess
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.models.institution import Institution, seed_default_institutions

client = TestClient(app)

def test_institution_db_model_persistence():
    """Verify institution model persists records across distinct database sessions."""
    # Session 1: Ensure seeded and create test institution
    with SessionLocal() as db1:
        seed_default_institutions(db1)
        vsb = db1.query(Institution).filter(Institution.id == "VSB_KARUR").first()
        assert vsb is not None
        assert vsb.name == "VSB Engineering College"
        assert vsb.campus_lat == settings.COLLEGE_DEPOT_LAT
        assert vsb.campus_lng == settings.COLLEGE_DEPOT_LON

        test_inst = Institution(
            id="INST_PERSIST_TEST",
            name="Session Persistence Test College",
            campus_code="SPTC",
            city="Trichy",
            district="Tiruchirappalli",
            state="Tamil Nadu",
            campus_lat=10.8284,
            campus_lng=78.6856,
            total_fleet_size=20,
            default_capacity=55,
            is_active=False,
            corridors=[{"id": "AREA_A", "name": "Trichy Radial", "bearing_deg": 45.0}],
        )
        db1.add(test_inst)
        db1.commit()

    # Session 2: Read from completely new session to prove persistence
    with SessionLocal() as db2:
        saved = db2.query(Institution).filter(Institution.id == "INST_PERSIST_TEST").first()
        assert saved is not None
        assert saved.name == "Session Persistence Test College"
        assert saved.city == "Trichy"
        assert saved.campus_lat == 10.8284
        assert saved.campus_lng == 78.6856
        assert len(saved.corridors) == 1

        # Cleanup test record
        db2.delete(saved)
        db2.commit()

def test_seed_default_institutions_idempotent():
    """Verify calling seeder repeatedly is idempotent and does not create duplicates."""
    with SessionLocal() as db:
        seed_default_institutions(db)
        seed_default_institutions(db)
        seed_default_institutions(db)

        vsb_count = db.query(Institution).filter(Institution.id == "VSB_KARUR").count()
        assert vsb_count == 1

def test_api_institution_persistence_and_active_switching(admin_headers):
    """Verify institutions created and switched via API persist to database."""
    payload = {
        "name": "Bannari Amman Institute of Technology",
        "campus_code": "BIT-SAT",
        "city": "Sathyamangalam",
        "district": "Erode",
        "campus_lat": 11.5034,
        "campus_lng": 77.2764,
        "total_fleet_size": 25,
        "default_capacity": 55,
    }
    res_create = client.post("/api/institutions", json=payload, headers=admin_headers)
    assert res_create.status_code == 200
    created_id = res_create.json()["institution"]["id"]

    # Verify created record in a fresh database session
    with SessionLocal() as db:
        db_inst = db.query(Institution).filter(Institution.id == created_id).first()
        assert db_inst is not None
        assert db_inst.name == "Bannari Amman Institute of Technology"
        assert db_inst.is_active is True

    # Switch active back to VSB_KARUR
    res_switch = client.post(
        "/api/institutions/active",
        json={"institution_id": "VSB_KARUR"},
        headers=admin_headers,
    )
    assert res_switch.status_code == 200
    assert res_switch.json()["active_institution"]["id"] == "VSB_KARUR"

    # Confirm active state in fresh DB session
    with SessionLocal() as db:
        vsb = db.query(Institution).filter(Institution.id == "VSB_KARUR").first()
        assert vsb.is_active is True
        bit = db.query(Institution).filter(Institution.id == created_id).first()
        assert bit.is_active is False

        # Cleanup
        db.delete(bit)
        db.commit()

def test_canonical_campus_coordinates_match_settings():
    """Verify GET /api/institutions/active returns canonical coordinates (M-02)."""
    res = client.get("/api/institutions/active")
    assert res.status_code == 200
    active = res.json()
    assert active["id"] == "VSB_KARUR"
    assert active["campus_lat"] == settings.COLLEGE_DEPOT_LAT
    assert active["campus_lng"] == settings.COLLEGE_DEPOT_LON
    assert active["campus_lat"] == 10.95488
    assert active["campus_lng"] == 77.95462

def test_institution_validation_bounds(admin_headers):
    """Verify coordinate bounds validation and 404 on missing institution."""
    # Out-of-bounds latitude (>90)
    invalid_lat = {
        "name": "Invalid Lat Campus",
        "city": "Nowhere",
        "campus_lat": 95.0,
        "campus_lng": 77.0,
    }
    res = client.post("/api/institutions", json=invalid_lat, headers=admin_headers)
    assert res.status_code == 422

    # Out-of-bounds longitude (<-180)
    invalid_lng = {
        "name": "Invalid Lng Campus",
        "city": "Nowhere",
        "campus_lat": 10.0,
        "campus_lng": -190.0,
    }
    res = client.post("/api/institutions", json=invalid_lng, headers=admin_headers)
    assert res.status_code == 422

    # Switch to non-existent institution
    res_404 = client.post(
        "/api/institutions/active",
        json={"institution_id": "NON_EXISTENT_ID"},
        headers=admin_headers,
    )
    assert res_404.status_code == 404

def test_list_districts_and_filtering():
    """Verify listing districts and district-filtered search."""
    res_dist = client.get("/api/institutions/districts")
    assert res_dist.status_code == 200
    districts = res_dist.json()["districts"]
    assert "All Districts" in districts
    assert "Karur" in districts

    # Filter by district
    res_filt = client.get("/api/institutions?district=Karur")
    assert res_filt.status_code == 200
    insts = res_filt.json()["institutions"]
    assert any(i["id"] == "VSB_KARUR" for i in insts)

def test_seed_preserves_active_when_other_institution_exists():
    """Verify seeding default VSB does not hijack active state if another campus is active."""
    with SessionLocal() as db:
        # Create an alternative active institution
        alt_inst = Institution(
            id="INST_OTHER_ACTIVE",
            name="Other Active University",
            campus_code="OAU",
            city="Coimbatore",
            district="Coimbatore",
            state="Tamil Nadu",
            campus_lat=11.0168,
            campus_lng=76.9558,
            total_fleet_size=30,
            default_capacity=55,
            is_active=True,
        )
        # Deactivate existing
        db.query(Institution).update({Institution.is_active: False})
        db.add(alt_inst)

        # Temporarily remove VSB
        vsb = db.query(Institution).filter(Institution.id == "VSB_KARUR").first()
        if vsb:
            db.delete(vsb)
        db.commit()

        # Seed when table contains other institutions and an active campus
        seeded_vsb = seed_default_institutions(db)
        assert seeded_vsb is not None
        assert seeded_vsb.id == "VSB_KARUR"
        # Must NOT be active because INST_OTHER_ACTIVE was active
        assert seeded_vsb.is_active is False

        active_inst = db.query(Institution).filter(Institution.is_active == True).first()
        assert active_inst.id == "INST_OTHER_ACTIVE"

        # Restore: activate VSB, remove alt_inst
        seeded_vsb.is_active = True
        db.delete(alt_inst)
        db.commit()

def test_cross_process_persistence():
    """Verify that records committed to the database persist across separate OS processes."""
    code = (
        "import json; "
        "from backend.app.database import SessionLocal; "
        "from backend.app.models.institution import Institution; "
        "db = SessionLocal(); "
        "inst = db.query(Institution).filter(Institution.id == 'VSB_KARUR').first(); "
        "out = {'id': inst.id, 'name': inst.name, 'campus_lat': inst.campus_lat, 'campus_lng': inst.campus_lng} if inst else {}; "
        "print(json.dumps(out)); "
        "db.close()"
    )
    result = subprocess.check_output([sys.executable, "-c", code], text=True)
    data = json.loads(result.strip())
    assert data.get("id") == "VSB_KARUR"
    assert data.get("name") == "VSB Engineering College"
    assert data.get("campus_lat") == 10.95488
    assert data.get("campus_lng") == 77.95462
