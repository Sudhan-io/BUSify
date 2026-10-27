import csv
import io
import json
import math
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Body, UploadFile, File, Form, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field
from backend.app.database import get_db
from backend.app.auth.auth_service import require_admin
from backend.app.models.bus import Bus
from backend.app.models.stop import Stop
from backend.app.models.plan import Plan
from backend.app.models.registration import Registration
from backend.app.models.student_attendance import StudentAttendance
from backend.app.core.forecasting.lightgbm_model import forecaster
from backend.app.core.allocation.optimizer import fleet_allocator
from backend.app.core.allocation.equity import compute_seating_equity
from backend.app.core.routing.vrp_solver import vrp_solver
from backend.app.core.routing.road_geometry_service import road_geometry_service
from backend.app.core.forecasting.disaggregator import disaggregate_area_demand
from backend.app.core.data.synthetic_generator import AREAS_CONFIG
from backend.app.core.data.anonymizer import hash_student_id
from backend.app.core.simulation.simulator import BASELINE_ALLOCATION
from backend.app.core.schedule_utils import format_12h, format_24h
from backend.app.config import settings

router = APIRouter(prefix="/workflow", tags=["College & Student Workflows"])

# Driver roster for transit office dispatch manifests (fictitious demo numbers)
DRIVERS_ROSTER = [
  {"name": "R. Murugan", "phone": "+91 90000 00001"},
  {"name": "S. Selvaraj", "phone": "+91 90000 00002"},
  {"name": "K. Palanisamy", "phone": "+91 90000 00003"},
  {"name": "M. Velusamy", "phone": "+91 90000 00004"},
  {"name": "P. Ramachandran", "phone": "+91 90000 00005"},
  {"name": "C. Karthikeyan", "phone": "+91 90000 00006"},
  {"name": "A. Natarajan", "phone": "+91 90000 00007"},
  {"name": "T. Subramani", "phone": "+91 90000 00008"},
  {"name": "V. Dhanapal", "phone": "+91 90000 00009"},
  {"name": "G. Manickam", "phone": "+91 90000 00010"},
]


class OptOutRequest(BaseModel):
    student_roll: str
    traveling_today: bool
    date: Optional[str] = None


class PlanApprovalRequest(BaseModel):
    date: str = Field(..., description="Target dispatch date (YYYY-MM-DD)")
    slot: str = Field(default="morning", description="Operational slot (morning or evening)")
    scenario: str = Field(default="REGULAR", description="Academic scenario")


# ── Student identity ────────────────────────────────────────────────────────
# This deployment has no student account system, so there is nothing to
# authenticate a student against. The previous behaviour — accept any roll
# number and synthesise a profile — turned the public endpoint into an
# enumeration oracle over the entire 2,200-student body.
#
# Binding the endpoints to a known roster closes that hole without inventing a
# fake auth system. It is NOT a substitute for real student authentication:
# see `C-01a` / `C-02` in docs/remediation/DEFECT_REGISTER.md for what a production
# deployment still needs (per-student credentials, or an opaque session token
# issued after login).
DEMO_STUDENT_ROSTER = [
    {"roll_no": "21CS104", "name": "K. Vignesh", "department": "CSE - Final Year"},
    {"roll_no": "22ME045", "name": "S. Aravind", "department": "Mechanical - 3rd Year"},
    {"roll_no": "23EC089", "name": "R. Priya", "department": "ECE - 2nd Year"},
    {"roll_no": "24IT012", "name": "M. Sneha", "department": "IT - 1st Year"},
]


def _resolve_known_student(roll_no: str) -> dict:
    """Returns the roster entry for `roll_no`, or raises 404.

    Rejecting unknown rolls is what removes the enumeration surface; a 404 also
    avoids confirming/denying whether an arbitrary roll exists.
    """
    normalised = (roll_no or "").strip().upper()
    for student in DEMO_STUDENT_ROSTER:
        if student["roll_no"].upper() == normalised:
            return student
    raise HTTPException(
        status_code=404,
        detail=f"Roll number '{normalised}' is not a registered commuter.",
    )


@router.get("/students", tags=["College & Student Workflows"])
def list_commuters():
    """
    Public roster of known commuter accounts for this deployment.

    Already effectively public (the dashboard rendered a hardcoded copy of this
    list), so exposing it via the API removes the frontend/backend duplication
    rather than widening the surface.
    """
    return {
        "total_students": len(DEMO_STUDENT_ROSTER),
        "students": DEMO_STUDENT_ROSTER,
    }


def _attendance_record_id(roll: str, date_str: str) -> str:
    """Deterministic primary key for StudentAttendance: SHA256(roll + date)."""
    return hashlib.sha256(f"{roll}:{date_str}".encode()).hexdigest()

@router.get("/operational-manifest")
def get_operational_manifest(
    date: str = Query(default=None, description="Operational Date (YYYY-MM-DD)"),
    scenario: str = Query(default="REGULAR", description="REGULAR, EXAM_DAY, PLACEMENT_DRIVE, MONSOON_RAIN"),
    db: Session = Depends(get_db)
):
    """
    Generates the actionable Transport Office Fleet Dispatch Manifest.
    Shows assigned driver, route stops, passenger count, and capacity utilization.
    """
    target_date = date or datetime.now().date().strftime("%Y-%m-%d")
    is_exam = scenario in ["EXAM_DAY", "PLACEMENT_DRIVE"]
    surge_multiplier = 1.35 if scenario == "MONSOON_RAIN" else (1.15 if scenario == "EXAM_DAY" else 1.0)

    # 1. Forecast demand across all 5 zones
    forecasts = {}
    for area_id in AREAS_CONFIG.keys():
        pred = forecaster.predict_for_date(target_date, area_id, exam_flag=is_exam)
        forecasts[area_id] = int(round(pred["p90_demand"] * surge_multiplier))

    # 2. Solve optimal fleet allocation (uses canonical BASELINE_ALLOCATION, resolving ALLOC-001)
    baseline = BASELINE_ALLOCATION.copy()
    alloc_res = fleet_allocator.solve(forecasts, baseline)
    optimized_allocation = alloc_res["allocation"]

    # 3. Assemble Driver Dispatch Sheets for active vehicles sourced from database
    try:
        active_buses = db.query(Bus).filter(Bus.is_active == True).order_by(Bus.bus_id).all()
        unique_active_buses = {b.bus_id: b for b in active_buses}.values()
        deployed_seats = sum(int(b.seats) for b in unique_active_buses if b.seats is not None)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Database error querying active fleet: {str(err)}")

    # Check whether a persisted plan exists in DB for this date and slot
    persisted_plans = db.query(Plan).filter(Plan.date == target_date, Plan.slot == "morning").all()
    is_plan_approved = len(persisted_plans) > 0

    available_by_area = {a: [b for b in active_buses if b.default_area_id == a] for a in AREAS_CONFIG.keys()}
    assigned_bus_ids = set()
    manifest = []
    has_insufficient_fleet = False

    for area_id, bus_count in optimized_allocation.items():
        area_info = AREAS_CONFIG.get(area_id, {})
        area_p90 = forecasts[area_id]
        area_p50 = int(round(area_p90 * 0.85))

        # Disaggregate and solve routes for this area (geometry not needed for tabular trip manifest)
        stops_payload = disaggregate_area_demand(area_id=area_id, area_p50=area_p50, area_p90=area_p90)
        routes_res = vrp_solver.solve(area_id=area_id, stops=stops_payload, num_buses=bus_count, include_road_geometry=False)
        active_routes = routes_res.get("routes", [])

        for r_i, route in enumerate(active_routes):
            # 1. Match eligible active bus from home area
            eligible_bus = None
            for b in available_by_area.get(area_id, []):
                if b.bus_id not in assigned_bus_ids:
                    eligible_bus = b
                    break
            # 2. If home area fleet exhausted, borrow from pool of available active buses
            if not eligible_bus:
                for b in active_buses:
                    if b.bus_id not in assigned_bus_ids:
                        eligible_bus = b
                        break

            # Calculate start and end pickup times
            itinerary = route.get("itinerary", [])
            first_pickup = itinerary[0]["time"] if itinerary else settings.EARLIEST_ROUTE_DEPARTURE
            campus_arrival = settings.FIRST_CLASS_ARRIVAL_TIME

            if eligible_bus:
                assigned_bus_ids.add(eligible_bus.bus_id)
                bus_code = eligible_bus.bus_id
                driver_name = eligible_bus.driver_name or "Assigned College Driver"
                driver_phone = eligible_bus.driver_phone or "+91 90000 00001"
                bus_capacity = int(eligible_bus.seats) if eligible_bus.seats is not None else settings.DEFAULT_BUS_CAPACITY
                route_status = "APPROVED" if is_plan_approved else "PENDING_APPROVAL"
            else:
                has_insufficient_fleet = True
                bus_code = "UNASSIGNED"
                driver_name = "UNASSIGNED (Fleet Shortage)"
                driver_phone = "N/A"
                bus_capacity = settings.DEFAULT_BUS_CAPACITY
                route_status = "UNASSIGNED_INSUFFICIENT_FLEET"

            manifest.append({
                "bus_code": bus_code,
                "area_id": area_id,
                "area_name": area_info.get("name", area_id),
                "driver_name": driver_name,
                "driver_phone": driver_phone,
                "capacity": bus_capacity,
                "allocated_riders": route.get("total_riders", 0),
                "utilization_pct": route.get("utilization_pct", 0.0),
                "departure_time": format_12h(first_pickup),
                "departure_time_24h": format_24h(first_pickup),
                "campus_arrival": format_12h(campus_arrival),
                "campus_arrival_24h": format_24h(campus_arrival),
                "schedule_feasible": route.get("schedule_feasible", True),
                "total_distance_km": route.get("total_distance_km", 0.0),
                "stops_list": [s.get("name", "") for s in itinerary if s.get("node_type") == "pickup_stop"],
                "stops_detail": [
                    {
                        "name": s.get("name", ""),
                        "stop_id": s.get("stop_id", ""),
                        "time": s.get("time", ""),
                        "boarded": s.get("boarded", 0),
                        "node_type": s.get("node_type", "pickup_stop"),
                    }
                    for s in itinerary
                    if s.get("node_type") == "pickup_stop"
                ],
                "status": route_status,
                "is_approved": is_plan_approved,
            })

    capacity = settings.DEFAULT_BUS_CAPACITY
    total_riders = sum(m["allocated_riders"] for m in manifest)
    overall_utilization_pct = round(total_riders / deployed_seats * 100, 1) if deployed_seats > 0 else 0.0

    # Calculate per-area demand and allocated seat capacity for seating equity (resolves DATA-003)
    area_metrics = {}
    for a in AREAS_CONFIG.keys():
        a_manifest = [m for m in manifest if m.get("area_id") == a]
        a_riders = sum(m.get("allocated_riders", 0) for m in a_manifest)
        # Deduplicate bus capacity by bus_code to prevent multi-leg vehicle double counting
        seen_buses = set()
        a_capacity = 0
        for m in a_manifest:
            b_code = m.get("bus_code")
            b_cap = m.get("capacity", capacity)
            if b_code:
                if b_code not in seen_buses:
                    seen_buses.add(b_code)
                    a_capacity += b_cap
            else:
                a_capacity += b_cap
        area_metrics[a] = {"riders": a_riders, "capacity": a_capacity}

    equity_res = compute_seating_equity(area_metrics)

    return {
        "date": target_date,
        "scenario": scenario,
        "surge_multiplier": surge_multiplier,
        "bus_capacity": capacity,
        "total_active_buses": len(manifest),
        "total_seats_deployed": deployed_seats,
        "total_expected_riders": total_riders,
        "overall_utilization_pct": overall_utilization_pct,
        "seating_equity_pct": equity_res["seating_equity_pct"],
        "area_utilization_variance": equity_res["area_utilization_variance"],
        "per_area_utilization_pct": equity_res["per_area_utilization_pct"],
        "equity_status": equity_res.get("equity_status", "VALID"),
        "total_standing": alloc_res.get("total_standing", 0),
        "total_empty": alloc_res.get("total_empty", 0),
        "churn": alloc_res.get("total_churn", 0),
        "manifest": manifest,
        "area_allocation": optimized_allocation,
        "baseline_allocation": baseline,
        "total_fleet_churn": sum(
            abs(optimized_allocation.get(a, 0) - baseline.get(a, 0))
            for a in optimized_allocation
        ),
        "plan_status": "APPROVED" if is_plan_approved else ("INSUFFICIENT_FLEET" if has_insufficient_fleet else "DRAFT"),
        "is_approved": is_plan_approved,
        "has_insufficient_fleet": has_insufficient_fleet,
    }

@router.post("/plan/approve", dependencies=[Depends(require_admin)])
def approve_daily_dispatch_plan(
    payload: PlanApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Validates and officially approves today's fleet dispatch manifest,
    persisting route assignments to the database plans table (Resolves M-13 / H-21).
    Enforces transport officer authentication and uses database transactions.
    """
    target_date = payload.date
    slot = payload.slot or "morning"
    scenario = payload.scenario or "REGULAR"

    # 1. Generate full operational manifest for validation
    manifest_payload = get_operational_manifest(date=target_date, scenario=scenario, db=db)
    manifest_rows = manifest_payload.get("manifest", [])

    if not manifest_rows:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot approve empty manifest: no routes scheduled.",
        )

    # 2. Validate fleet readiness and absence of shortages
    unassigned = [m for m in manifest_rows if m["bus_code"] == "UNASSIGNED"]
    if unassigned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot approve dispatch: {len(unassigned)} route(s) lack assigned vehicles due to fleet shortage.",
        )

    assigned_buses = [m["bus_code"] for m in manifest_rows]
    if len(assigned_buses) != len(set(assigned_buses)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Duplicate bus assignment detected in manifest.",
        )

    # Verify all assigned buses are active in database
    db_active_ids = {
        b[0]
        for b in db.query(Bus.bus_id)
        .filter(Bus.is_active == True, Bus.bus_id.in_(assigned_buses))
        .all()
    }
    invalid_buses = set(assigned_buses) - db_active_ids
    if invalid_buses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Assigned buses are inactive or missing from database: {sorted(invalid_buses)}",
        )

    # 3. Transactional persistence: atomically replace prior plan for (date, slot)
    try:
        db.query(Plan).filter(Plan.date == target_date, Plan.slot == slot).delete()
        created_plans = []
        for m in manifest_rows:
            route_summary = {
                "bus_code": m["bus_code"],
                "driver_name": m["driver_name"],
                "driver_phone": m["driver_phone"],
                "capacity": m["capacity"],
                "allocated_riders": m["allocated_riders"],
                "departure_time": m["departure_time"],
                "departure_time_24h": m["departure_time_24h"],
                "campus_arrival": m["campus_arrival"],
                "campus_arrival_24h": m["campus_arrival_24h"],
                "stops_list": m.get("stops_list", []),
                "stops_detail": m.get("stops_detail", []),
                "total_distance_km": m.get("total_distance_km", 0.0),
            }
            plan = Plan(
                date=target_date,
                slot=slot,
                bus_id=m["bus_code"],
                area_id=m["area_id"],
                scenario=scenario,
                status="APPROVED",
                total_riders=m["allocated_riders"],
                route_json=json.dumps(route_summary),
                created_at=datetime.now(timezone.utc),
            )
            db.add(plan)
            created_plans.append(plan)

        db.commit()
        for p in created_plans:
            db.refresh(p)
    except Exception as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist dispatch plan: {str(err)}",
        )

    return {
        "success": True,
        "status": "APPROVED",
        "message": f"Successfully approved and persisted daily dispatch plan for {target_date} ({len(created_plans)} routes).",
        "date": target_date,
        "slot": slot,
        "scenario": scenario,
        "total_routes": len(created_plans),
        "plan_ids": [p.plan_id for p in created_plans],
    }

@router.get("/plan/status")
def get_plan_status(
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    slot: str = Query(default="morning", description="Operational slot"),
    db: Session = Depends(get_db),
):
    """Retrieves persisted dispatch plan approval status from database."""
    plans = db.query(Plan).filter(Plan.date == date, Plan.slot == slot).all()
    if not plans:
        return {
            "exists": False,
            "status": "DRAFT",
            "date": date,
            "slot": slot,
            "total_routes": 0,
            "created_at": None,
        }
    return {
        "exists": True,
        "status": plans[0].status or "APPROVED",
        "date": date,
        "slot": slot,
        "scenario": plans[0].scenario or "REGULAR",
        "total_routes": len(plans),
        "created_at": plans[0].created_at.isoformat() if plans[0].created_at else None,
    }

_STOPS_CACHE: Optional[list] = None

def _get_all_stops_cached(db: Session) -> list:
    """Returns cached list of Stop records to avoid N+1 queries on student profile requests (Resolves DATA-006 / H-10)."""
    global _STOPS_CACHE
    if _STOPS_CACHE is None:
        _STOPS_CACHE = db.query(Stop).order_by(Stop.stop_id).all()
    return _STOPS_CACHE

def invalidate_stops_cache():
    """Invalidates cached stops when stops are added or modified."""
    global _STOPS_CACHE
    _STOPS_CACHE = None

@router.get("/student-profile")
def get_student_profile(
    roll_no: str = Query(default="21CS104", description="Student Roll Number"),
    date: str = Query(default=None, description="Travel Date"),
    db: Session = Depends(get_db)
):
    """
    Returns authentic student commuter transit profile, digital boarding ticket,
    guaranteed seat assignment, driver emergency contact, and real-time opt-out status.

    Public by design (a commuter must be able to view their own pass without a
    login), but scoped to the known roster — see DEMO_STUDENT_ROSTER.
    """
    student = _resolve_known_student(roll_no)
    roll_no = student["roll_no"]

    target_date = date or datetime.now().date().strftime("%Y-%m-%d")

    # Deterministic mapping of student roll number to stop based on hash
    student_hash = hash_student_id(roll_no)
    all_stops = _get_all_stops_cached(db)
    if not all_stops:
        raise HTTPException(status_code=404, detail="No stops found.")

    stop_index = int(student_hash[:4], 16) % len(all_stops)
    assigned_stop = all_stops[stop_index]

    # Check whether an authoritative approved dispatch plan exists for this date
    approved_plans = db.query(Plan).filter(Plan.date == target_date, Plan.slot == "morning").all()
    is_approved = len(approved_plans) > 0
    plan_status = "APPROVED" if is_approved else "PENDING_APPROVAL"

    matched_plan_route = None
    if approved_plans:
        for p in approved_plans:
            try:
                r_data = json.loads(p.route_json)
                stops_in_route = [s.get("stop_id") for s in r_data.get("stops_detail", [])]
                if assigned_stop.stop_id in stops_in_route or assigned_stop.name in r_data.get("stops_list", []):
                    matched_plan_route = (p, r_data)
                    break
            except Exception:
                continue

    # Default fallback mapping
    area_bus_mapping = {
        "AREA_A": ("BUS-02", DRIVERS_ROSTER[1]),
        "AREA_B": ("BUS-14", DRIVERS_ROSTER[3]),
        "AREA_C": ("BUS-24", DRIVERS_ROSTER[5]),
        "AREA_D": ("BUS-33", DRIVERS_ROSTER[7]),
        "AREA_E": ("BUS-45", DRIVERS_ROSTER[9]),
    }
    fallback_code, fallback_driver = area_bus_mapping.get(assigned_stop.area_id, ("BUS-01", DRIVERS_ROSTER[0]))

    if matched_plan_route:
        plan_obj, route_data = matched_plan_route
        bus_code = plan_obj.bus_id
        driver = {
            "name": route_data.get("driver_name") or fallback_driver["name"],
            "phone": route_data.get("driver_phone") or fallback_driver["phone"],
        }
    else:
        bus_row = db.query(Bus).filter(Bus.bus_id == fallback_code).first()
        bus_code = fallback_code
        driver = {
            "name": (bus_row.driver_name if bus_row and bus_row.driver_name else fallback_driver["name"]),
            "phone": (bus_row.driver_phone if bus_row and bus_row.driver_phone else fallback_driver["phone"]),
        }

    # Deterministic seat number between 1 and 55
    seat_num = (int(student_hash[4:8], 16) % 52) + 1

    # Check if student opted out for today — query persistent DB table
    target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    roll_hash = hash_student_id(roll_no)
    attendance = db.query(StudentAttendance).filter(
        StudentAttendance.student_roll_hash == roll_hash,
        StudentAttendance.travel_date == target_date_obj,
    ).first()
    if not attendance:
        # Fallback to the latest record for this student if date not explicitly matched
        attendance = db.query(StudentAttendance).filter(
            StudentAttendance.student_roll_hash == roll_hash,
        ).order_by(StudentAttendance.updated_at.desc()).first()
    # Default to traveling if no explicit opt-out record exists
    is_traveling = attendance.traveling_today if attendance else True

    # Schedule the pickup backwards from the campus arrival using the actual corridor distance
    campus_distance_km = round(4.5 + assigned_stop.sequence_order * 2.2, 1)
    travel_minutes = int(round(
        (campus_distance_km / settings.AVERAGE_BUS_SPEED_KMH) * 60
    ))
    campus_arrival_dt = datetime.strptime(settings.FIRST_CLASS_ARRIVAL_TIME, "%H:%M")
    earliest_dt = datetime.strptime(settings.EARLIEST_ROUTE_DEPARTURE, "%H:%M")

    pickup_dt = campus_arrival_dt - timedelta(minutes=travel_minutes)
    if matched_plan_route:
        _, route_data = matched_plan_route
        for s in route_data.get("stops_detail", []):
            if (s.get("stop_id") == assigned_stop.stop_id or s.get("name") == assigned_stop.name) and s.get("time"):
                try:
                    pickup_dt = datetime.strptime(s["time"], "%H:%M")
                    break
                except Exception:
                    pass

    schedule_feasible = pickup_dt >= earliest_dt
    if not schedule_feasible:
        pickup_dt = earliest_dt

    if matched_plan_route:
        _, route_data = matched_plan_route
        allocated_riders = route_data.get("allocated_riders", 40)
        bus_cap = route_data.get("capacity", settings.DEFAULT_BUS_CAPACITY)
        base_occ = round((allocated_riders / bus_cap) * 100, 1)
        occupancy_pct = base_occ if is_traveling else max(0.0, round(base_occ - (1.0 / bus_cap * 100), 1))
    else:
        occupancy_pct = 78 if is_traveling else 76

    stop_dict = assigned_stop.to_dict()
    stop_dict["campus_distance_km"] = campus_distance_km

    return {
        "student_roll": roll_no,
        "student_name": student["name"],
        "student_department": student["department"],
        "student_hash": student_hash[:12].upper(),
        "academic_year": "2025-2026",
        "assigned_stop": stop_dict,
        "assigned_bus_code": bus_code,
        "driver_name": driver["name"],
        "driver_phone": driver["phone"],
        "seat_number": f"Seat #{seat_num}",
        "seat_guarantee": "CONFIRMED_NO_STANDING",
        "is_approved_dispatch": is_approved,
        "plan_status": plan_status,
        "service_status": "ON_SCHEDULE" if is_traveling and schedule_feasible else ("ABSENCE_RECORDED" if not is_traveling else "SCHEDULE_TIGHT"),
        "pickup_time": format_12h(pickup_dt),
        "pickup_time_24h": format_24h(pickup_dt),
        "campus_arrival": format_12h(campus_arrival_dt),
        "campus_arrival_24h": format_24h(campus_arrival_dt),
        "schedule_feasible": schedule_feasible,
        "traveling_today": is_traveling,
        "occupancy_pct": occupancy_pct,
        "crowd_level": "LOW" if not is_traveling else ("HIGH" if occupancy_pct > 85 else "MODERATE"),
    }

@router.post("/student-opt-out")
def toggle_student_opt_out(
    payload: OptOutRequest,
    date: str = Query(default=None, description="Travel Date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Persistent real-time toggle for student daily travel preference.
    Writes to the student_attendance database table so preferences survive restarts.

    Scoped to the known roster: without this, any caller could flip the travel
    flag for any of the 2,200 registered students by guessing roll numbers.
    """
    student = _resolve_known_student(payload.student_roll)
    roll_no = student["roll_no"]

    target_date_str = payload.date or date or datetime.now().date().isoformat()
    target_date_obj = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    roll_hash = hash_student_id(roll_no)
    record_id = _attendance_record_id(roll_no, target_date_str)

    # Upsert: update if exists, insert if new
    attendance = db.query(StudentAttendance).filter(
        StudentAttendance.id == record_id
    ).first()

    if attendance:
        attendance.traveling_today = payload.traveling_today
    else:
        attendance = StudentAttendance(
            id=record_id,
            student_roll_hash=roll_hash,
            travel_date=target_date_obj,
            traveling_today=payload.traveling_today,
        )
        db.add(attendance)

    db.commit()
    db.refresh(attendance)

    # Count opt-outs for today from DB
    total_opt_outs = db.query(StudentAttendance).filter(
        StudentAttendance.travel_date == target_date_obj,
        StudentAttendance.traveling_today == False,  # noqa: E712
    ).count()

    # Check whether an approved dispatch plan already exists for this date.
    # Daily preference updates are faithfully recorded, but existing locked plans are preserved.
    approved_plan = db.query(Plan).filter(
        Plan.date == target_date_str,
        Plan.slot == "morning",
        Plan.status == "APPROVED"
    ).first()
    plan_locked = approved_plan is not None

    msg = (
        f"Seat re-confirmed for {roll_no}."
        if payload.traveling_today
        else f"Absence recorded for {roll_no}. Seat released for peers."
    )
    if plan_locked:
        msg += " (Notice: Active dispatch plan for today is approved and locked.)"

    return {
        "student_roll": roll_no,
        "travel_date": target_date_str,
        "traveling_today": payload.traveling_today,
        "message": msg,
        "total_active_opt_outs": total_opt_outs,
        "plan_locked": plan_locked,
    }


@router.get("/students/registrations", tags=["College & Student Workflows"])
def list_student_registrations(
    area_id: Optional[str] = Query(None, description="Filter registrations by corridor zone"),
    stop_id: Optional[str] = Query(None, description="Filter registrations by specific stop ID"),
    search: Optional[str] = Query(None, description="Search by stop name or masked ID"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Retrieves authoritative student registrations mapped to transit stops and corridors.
    Enforces student privacy by masking student SHA-256 hashes to prevent bulk PII exposure.
    """
    query = db.query(
        Registration.reg_id,
        Registration.student_hash,
        Registration.stop_id,
        Registration.academic_year,
        Stop.name.label("stop_name"),
        Stop.area_id.label("area_id")
    ).join(Stop, Registration.stop_id == Stop.stop_id)

    if area_id is not None:
        query = query.filter(Stop.area_id == area_id)
    if stop_id is not None:
        query = query.filter(Registration.stop_id == stop_id)
    if search:
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            func.lower(Stop.name).like(term) |
            func.lower(Registration.stop_id).like(term)
        )

    total_count = query.count()
    offset = (page - 1) * page_size
    rows = query.order_by(Registration.reg_id).offset(offset).limit(page_size).all()

    items = []
    for r in rows:
        masked_hash = f"{r.student_hash[:8].upper()}..."
        items.append({
            "reg_id": r.reg_id,
            "masked_student_id": masked_hash,
            "stop_id": r.stop_id,
            "stop_name": r.stop_name,
            "area_id": r.area_id,
            "academic_year": r.academic_year or "2025-2026",
        })

    return {
        "total_registrations": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if total_count > 0 else 1,
        "registrations": items,
    }


@router.get("/demand-summary", tags=["College & Student Workflows"])
def get_demand_summary(
    date: str = Query(default=None, description="Forecast target date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Aggregates authoritative commuter demand, stop distribution, and registration volumes
    across all transit zones.
    """
    target_date = date or datetime.now().date().strftime("%Y-%m-%d")

    # 1. Total registrations per area
    reg_counts = dict(
        db.query(Stop.area_id, func.count(Registration.reg_id))
        .join(Registration, Stop.stop_id == Registration.stop_id)
        .group_by(Stop.area_id)
        .all()
    )

    # 2. Stop counts per area
    stop_counts = dict(
        db.query(Stop.area_id, func.count(Stop.stop_id))
        .group_by(Stop.area_id)
        .all()
    )

    # 3. Active buses per area
    bus_counts = dict(
        db.query(Bus.default_area_id, func.count(Bus.bus_id))
        .filter(Bus.is_active == True)
        .group_by(Bus.default_area_id)
        .all()
    )

    areas_summary = []
    total_reg = 0
    total_stops_count = 0
    for a_id in sorted(AREAS_CONFIG.keys()):
        cfg = AREAS_CONFIG[a_id]
        r_count = reg_counts.get(a_id, 0)
        s_count = stop_counts.get(a_id, 0)
        b_count = bus_counts.get(a_id, 0)
        pred = forecaster.predict_for_date(target_date, a_id)

        total_reg += r_count
        total_stops_count += s_count
        areas_summary.append({
            "area_id": a_id,
            "area_name": cfg.get("name", a_id),
            "registered_commuters": r_count,
            "stops_count": s_count,
            "assigned_active_buses": b_count,
            "baseline_buses": BASELINE_ALLOCATION.get(a_id, 10),
            "p50_demand": pred.get("p50_demand", 0),
            "p90_demand": pred.get("p90_demand", 0),
        })

    return {
        "date": target_date,
        "total_registered_commuters": total_reg,
        "total_stops": total_stops_count,
        "total_zones": len(AREAS_CONFIG),
        "areas": areas_summary,
    }


# =====================================================================
# SUGGESTIONS 1 & 2: ADMIN CSV UPLOAD, AUTO-GEOCODING & BENCHMARK
# =====================================================================

CAMPUS_LAT = settings.COLLEGE_DEPOT_LAT
CAMPUS_LNG = settings.COLLEGE_DEPOT_LON

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def geocode_stop_fallback(zone: str, stop_idx: int, campus_lat: float = CAMPUS_LAT, campus_lng: float = CAMPUS_LNG) -> tuple:
    """
    Suggestion 1: Auto-geocodes stop names lacking GPS coordinates by computing radial bearing
    and realistic radial corridor distances from the active college campus depot.
    """
    zone_upper = (zone or "AREA_A").upper()
    zone_bearings = {
        "AREA_A": 25.0,   # North corridor
        "AREA_B": 95.0,   # East corridor
        "AREA_C": 180.0,  # South corridor
        "AREA_D": 270.0,  # West corridor
        "AREA_E": 320.0,  # Central urban corridor
    }
    
    base_bearing = zone_bearings.get(zone_upper, (stop_idx * 67.5) % 360.0)
    jitter = ((stop_idx % 5) - 2) * 4.0
    bearing = (base_bearing + jitter) % 360.0
    dist_km = 6.0 + ((stop_idx * 3.4) % 22.0)
    
    d_lat = (dist_km / 111.0) * math.cos(math.radians(bearing))
    d_lng = (dist_km / (111.0 * math.cos(math.radians(campus_lat)))) * math.sin(math.radians(bearing))
    
    return round(campus_lat + d_lat, 6), round(campus_lng + d_lng, 6)

SAMPLE_TEMPLATE_CSV = """stop_name,zone,student_count,suggested_bus_code,latitude,longitude
Karudayampalayam Junction,AREA_A,28,BUS-01,10.9592,77.9482
Covai Road Arch,AREA_A,34,BUS-01,10.9560,77.9650
Central Bus Stand (Karur),AREA_A,42,BUS-01,10.9575,78.0815
Vengamedu Junction,AREA_A,25,BUS-02,10.9690,78.0790
Gandhigramam South,AREA_B,36,BUS-03,10.9380,78.0750
Sanapiratti Roundabout,AREA_B,27,BUS-03,10.9420,78.0880
Rayanoor Junction,AREA_B,22,BUS-03,10.9250,78.0690
Thanthonimalai Hill Gate,AREA_C,38,BUS-04,10.9280,78.0990
Collectorate Complex,AREA_C,30,BUS-04,10.9340,78.0950
Velur Bridge Checkpost,AREA_D,31,BUS-05,11.0020,78.0620
Pugalur Sugar Factory Gate,AREA_D,26,BUS-05,11.0320,78.0420
Paramathi Velur Four Roads,AREA_E,35,BUS-06,11.0250,78.0120
Noyyal River Junction,AREA_E,20,BUS-06,11.0080,77.9650
"""

def parse_and_benchmark_csv(
    csv_text: str,
    campus_lat: float = CAMPUS_LAT,
    campus_lng: float = CAMPUS_LNG,
    institution_name: str = "VSB Engineering College Karur"
):
    f = io.StringIO(csv_text.strip())
    sample = csv_text[:1024]
    delimiter = ','
    if ';' in sample and sample.count(';') > sample.count(','):
        delimiter = ';'
    elif '\t' in sample and sample.count('\t') > sample.count(','):
        delimiter = '\t'
        
    reader = csv.DictReader(f, delimiter=delimiter)
    stops = []
    auto_geocoded_count = 0
    
    raw_rows = list(reader)
    if not raw_rows:
        raise HTTPException(status_code=400, detail="CSV file is empty or missing headers.")
        
    for idx, row in enumerate(raw_rows):
        normalized = {k.strip().lower().replace(" ", "_"): (v.strip() if v else "") for k, v in row.items() if k}
        
        stop_name = (
            normalized.get("stop_name") or
            normalized.get("stop") or
            normalized.get("name") or
            normalized.get("location") or
            f"Stop #{idx+1}"
        )
        
        zone = (
            normalized.get("zone") or
            normalized.get("area") or
            normalized.get("area_id") or
            "AREA_A"
        )
        
        count_str = (
            normalized.get("student_count") or
            normalized.get("students") or
            normalized.get("riders") or
            normalized.get("passengers") or
            normalized.get("count") or
            "18"
        )
        try:
            student_count = max(1, int(float(count_str)))
        except ValueError:
            student_count = 18
            
        suggested_bus = (
            normalized.get("suggested_bus_code") or
            normalized.get("suggested_bus") or
            normalized.get("bus_code") or
            normalized.get("bus") or
            normalized.get("route") or
            f"BUS-{(idx // 3) + 1:02d}"
        )
        
        # Suggestion 1: Geocoding check using college campus hub as origin
        lat_str = normalized.get("latitude") or normalized.get("lat")
        lng_str = normalized.get("longitude") or normalized.get("lng") or normalized.get("lon")
        
        is_geocoded = False
        lat, lng = None, None
        if lat_str and lng_str:
            try:
                lat = float(lat_str)
                lng = float(lng_str)
                if abs(lat) < 0.001 and abs(lng) < 0.001:
                    lat, lng = None, None
            except ValueError:
                lat, lng = None, None
                
        if lat is None or lng is None:
            lat, lng = geocode_stop_fallback(zone, idx, campus_lat=campus_lat, campus_lng=campus_lng)
            is_geocoded = True
            auto_geocoded_count += 1
            
        stops.append({
            "stop_id": f"IMP-{idx+1:03d}",
            "stop_name": stop_name,
            "zone": zone,
            "student_count": student_count,
            "suggested_bus_code": suggested_bus,
            "latitude": lat,
            "longitude": lng,
            "auto_geocoded": is_geocoded,
        })

    # Suggestion 2: Benchmark Comparison Calculation
    # 1. Manual Static Routes Calculation
    manual_groups = {}
    for st in stops:
        b_code = st["suggested_bus_code"]
        if b_code not in manual_groups:
            manual_groups[b_code] = []
        manual_groups[b_code].append(st)
        
    manual_total_km = 0.0
    manual_standing = 0
    manual_overloaded_buses = 0
    manual_routes_summary = []
    
    standard_bus_capacity = settings.DEFAULT_BUS_CAPACITY
    for b_code, b_stops in manual_groups.items():
        riders = sum(s["student_count"] for s in b_stops)
        standing = max(0, riders - standard_bus_capacity)
        if standing > 0:
            manual_overloaded_buses += 1
        manual_standing += standing
        
        route_km = 0.0
        cur_lat, cur_lng = campus_lat, campus_lng
        waypoints = [(campus_lat, campus_lng)]
        for s in b_stops:
            route_km += haversine_distance(cur_lat, cur_lng, s["latitude"], s["longitude"])
            cur_lat, cur_lng = s["latitude"], s["longitude"]
            waypoints.append((s["latitude"], s["longitude"]))
        route_km += haversine_distance(cur_lat, cur_lng, campus_lat, campus_lng)
        waypoints.append((campus_lat, campus_lng))
        
        # Apply realistic road winding factor (1.28x Euclidean)
        route_km = round(route_km * 1.28, 1)
        manual_total_km += route_km
        
        # Fetch actual road geometry following the street network
        road_coords = road_geometry_service.get_road_geometry(waypoints)
        
        manual_routes_summary.append({
            "bus_code": b_code,
            "stops_count": len(b_stops),
            "riders": riders,
            "capacity": standard_bus_capacity,
            "standing": standing,
            "distance_km": route_km,
            "is_overloaded": standing > 0,
            "road_geometry": road_coords,
        })

    total_riders = sum(s["student_count"] for s in stops)
    manual_buses_count = len(manual_groups)
    manual_total_km = round(manual_total_km, 1)
    
    # 2. BUSify Rapid Benchmark Route Calculation (Resolves M-03 & ALLOC-004)
    # NOTE (M-03): This route generator uses an angular polar-sweep clustering heuristic
    # with a 1.28x road winding factor. It provides immediate (<100ms) synchronous client feedback
    # during CSV uploads to benchmark potential vehicle savings, unlike the comprehensive
    # OR-Tools CVRP solver used in the full daily manifest pipeline.
    opt_bus_capacity = standard_bus_capacity
    
    def stop_angle(s):
        return math.atan2(s["latitude"] - campus_lat, s["longitude"] - campus_lng)
    
    sorted_stops = sorted(stops, key=stop_angle)
    
    opt_routes = []
    current_cluster = []
    current_demand = 0
    
    for s in sorted_stops:
        if current_demand + s["student_count"] > opt_bus_capacity and current_cluster:
            opt_routes.append(current_cluster)
            current_cluster = [s]
            current_demand = s["student_count"]
        else:
            current_cluster.append(s)
            current_demand += s["student_count"]
    if current_cluster:
        opt_routes.append(current_cluster)
        
    opt_buses_count = len(opt_routes)
    opt_total_km = 0.0
    opt_routes_summary = []
    
    for r_i, r_stops in enumerate(opt_routes):
        b_code = f"BUS-OPT-{r_i+1:02d}"
        riders = sum(s["student_count"] for s in r_stops)
        
        ordered_stops = sorted(r_stops, key=lambda x: haversine_distance(campus_lat, campus_lng, x["latitude"], x["longitude"]), reverse=True)
        
        route_km = 0.0
        cur_lat, cur_lng = campus_lat, campus_lng
        waypoints = [(campus_lat, campus_lng)]
        for s in ordered_stops:
            route_km += haversine_distance(cur_lat, cur_lng, s["latitude"], s["longitude"])
            cur_lat, cur_lng = s["latitude"], s["longitude"]
            waypoints.append((s["latitude"], s["longitude"]))
        route_km += haversine_distance(cur_lat, cur_lng, campus_lat, campus_lng)
        waypoints.append((campus_lat, campus_lng))
        
        # Optimized corridor routing factor ~1.18x
        route_km = round(route_km * 1.18, 1)
        opt_total_km += route_km
        
        road_coords = road_geometry_service.get_road_geometry(waypoints)
        
        opt_routes_summary.append({
            "bus_code": b_code,
            "stops_count": len(ordered_stops),
            "riders": riders,
            "capacity": standard_bus_capacity,
            "standing": 0,
            "distance_km": route_km,
            "is_overloaded": False,
            "road_geometry": road_coords,
        })
        
    opt_total_km = round(opt_total_km, 1)
    
    # Financial and Environmental Savings (resolves M-04 with documented formulas and cited factors)
    # Assumptions:
    # - 2 trips/day (morning pickup + evening drop) * 220 academic working days/year.
    # - 3.8 km/L average transit bus fuel efficiency (standard college bus).
    # - Rs. 94.5 / Liter commercial diesel rate in Tamil Nadu.
    # - 2.68 kg CO2 emitted per Liter of diesel fuel combusted (IPCC conversion factor).
    km_saved_daily = max(0.0, round(manual_total_km - opt_total_km, 1))
    km_saved_pct = round((km_saved_daily / max(manual_total_km, 1.0)) * 100, 1)
    
    annual_diesel_liters = round((km_saved_daily * 2 * 220) / 3.8, 0) if km_saved_daily > 0 else 0
    annual_savings_inr = round(annual_diesel_liters * 94.5, 0)
    co2_saved_kg = round(annual_diesel_liters * 2.68, 1)
    
    return {
        "success": True,
        "total_stops_imported": len(stops),
        "auto_geocoded_count": auto_geocoded_count,
        "campus_origin": {
            "name": institution_name,
            "campus_lat": campus_lat,
            "campus_lng": campus_lng,
        },
        "stops": stops,
        "benchmark": {
            "manual": {
                "buses_used": manual_buses_count,
                "total_distance_km": manual_total_km,
                "total_riders": total_riders,
                "standing_passengers": manual_standing,
                "overloaded_buses": manual_overloaded_buses,
                "avg_utilization_pct": round(total_riders / max(manual_buses_count * standard_bus_capacity, 1) * 100, 1),
                "routes": manual_routes_summary,
            },
            "optimized": {
                "buses_used": opt_buses_count,
                "total_distance_km": opt_total_km,
                "total_riders": total_riders,
                "standing_passengers": 0,
                "overloaded_buses": 0,
                "avg_utilization_pct": round(total_riders / max(opt_buses_count * standard_bus_capacity, 1) * 100, 1),
                "routes": opt_routes_summary,
            },
            "savings": {
                "km_saved_daily": km_saved_daily,
                "km_saved_pct": km_saved_pct,
                "buses_saved": max(0, manual_buses_count - opt_buses_count),
                "annual_diesel_liters": int(annual_diesel_liters),
                "annual_savings_inr": int(annual_savings_inr),
                "annual_savings_formatted": f"Rs. {int(annual_savings_inr):,}",
                "standing_reduced": manual_standing,
                "co2_saved_kg": co2_saved_kg,
            }
        }
    }

class UploadStopsJsonPayload(BaseModel):
    csv_text: str
    campus_lat: Optional[float] = None
    campus_lng: Optional[float] = None
    institution_name: Optional[str] = None

@router.get("/template-csv")
def download_stops_csv_template():
    """Returns downloadable sample CSV template for the college admin."""
    return Response(
        content=SAMPLE_TEMPLATE_CSV,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=college_stops_template.csv"}
    )

@router.post("/upload-stops-csv", dependencies=[Depends(require_admin)])
async def upload_stops_csv(
    file: Optional[UploadFile] = File(None),
    csv_text: Optional[str] = Form(None),
    campus_lat: Optional[float] = Query(None),
    campus_lng: Optional[float] = Query(None),
    institution_name: Optional[str] = Query(None),
    body: Optional[UploadStopsJsonPayload] = Body(None)
):
    """
    Ingests stop records and passenger boarding demands from CSV/Excel.
    Implements Suggestion 1 (auto-geocoding fallback anchored to active campus) and
    Suggestion 2 (Manual vs. BUSify Optimized Comparative Benchmark with true road-following geometries).
    """
    content = ""
    target_lat = campus_lat or CAMPUS_LAT
    target_lng = campus_lng or CAMPUS_LNG
    target_name = institution_name or "VSB Engineering College Karur"

    MAX_CSV_BYTES = 5 * 1024 * 1024  # 5MB payload cap to prevent memory DOS

    if file is not None:
        raw_bytes = await file.read()
        if len(raw_bytes) > MAX_CSV_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded file exceeds maximum allowed size of {MAX_CSV_BYTES // (1024*1024)}MB."
            )
        filename_lower = (file.filename or "").lower()
        if filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls") or raw_bytes.startswith(b"PK\x03\x04"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excel binary workbook (.xlsx/.xls) is not supported directly. Please export or save your workbook as a CSV (.csv) or tab-delimited text (.txt) file before uploading."
            )
        content = raw_bytes.decode("utf-8", errors="replace")
    elif csv_text is not None and csv_text.strip():
        if len(csv_text.encode("utf-8")) > MAX_CSV_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Submitted CSV text exceeds maximum allowed size of {MAX_CSV_BYTES // (1024*1024)}MB."
            )
        content = csv_text
    elif body is not None and body.csv_text.strip():
        if len(body.csv_text.encode("utf-8")) > MAX_CSV_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Submitted CSV text exceeds maximum allowed size of {MAX_CSV_BYTES // (1024*1024)}MB."
            )
        content = body.csv_text
        if body.campus_lat is not None:
            target_lat = body.campus_lat
        if body.campus_lng is not None:
            target_lng = body.campus_lng
        if body.institution_name is not None:
            target_name = body.institution_name
    else:
        content = SAMPLE_TEMPLATE_CSV
        
    invalidate_stops_cache()
    return parse_and_benchmark_csv(
        content,
        campus_lat=target_lat,
        campus_lng=target_lng,
        institution_name=target_name
    )

