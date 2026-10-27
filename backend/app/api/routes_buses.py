from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from backend.app.database import get_db, engine
from backend.app.models.bus import Bus
from backend.app.models.plan import Plan
from backend.app.schemas import BusSchema, BusCreateRequest, BusUpdateRequest
from backend.app.auth.auth_service import require_admin
from backend.app.core.data.synthetic_generator import AREAS_CONFIG

router = APIRouter(tags=["Fleet Inventory"])


def _validate_area_id(area_id: str | None) -> str | None:
    """
    Rejects area identifiers the forecaster and allocator cannot handle.

    An unrecognised area reaches LabelEncoder.transform at prediction time and
    raises ValueError, which would surface as an opaque 500 on /crowding.
    Validating here keeps the failure at the boundary that introduced it.
    """
    if area_id is None:
        return None
    if area_id not in AREAS_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Unknown area_id '{area_id}'. "
                f"Valid areas: {sorted(AREAS_CONFIG.keys())}"
            ),
        )
    return area_id


def ensure_bus_columns():
    """Ensure optional fleet management columns exist in SQLite database."""
    try:
        with engine.connect() as conn:
            # Query column names for buses
            result = conn.execute(text("PRAGMA table_info(buses)")).fetchall()
            existing_cols = {row[1] for row in result}
            
            new_cols = [
                ("registration_no", "TEXT"),
                ("driver_name", "TEXT"),
                ("driver_phone", "TEXT"),
                ("depot_location", "TEXT"),
                ("route_name", "TEXT"),
            ]
            for col_name, col_type in new_cols:
                if col_name not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE buses ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                    except Exception:
                        pass
    except Exception as e:
        print(f"Column migration notice: {e}")

_ensure_bus_columns = ensure_bus_columns


@router.get("/buses/drivers", tags=["Fleet & Driver Inventory"])
def list_drivers(
    is_active: Optional[bool] = Query(None, description="Filter drivers by active status"),
    area_id: Optional[str] = Query(None, description="Filter drivers by default corridor"),
    search: Optional[str] = Query(None, description="Search driver name or phone"),
    db: Session = Depends(get_db)
):
    """
    Retrieves the authoritative roster of college drivers from active fleet vehicles.
    Provides single source of truth for driver assignments, contact details, and route corridors.
    """
    query = db.query(Bus)
    if is_active is not None:
        query = query.filter(Bus.is_active == is_active)
    if area_id is not None:
        _validate_area_id(area_id)
        query = query.filter(Bus.default_area_id == area_id)
    if search:
        pattern = f"%{search.strip().lower()}%"
        query = query.filter(
            func.lower(Bus.driver_name).like(pattern) |
            func.lower(Bus.driver_phone).like(pattern) |
            func.lower(Bus.bus_id).like(pattern)
        )

    buses = query.order_by(Bus.bus_id).all()
    driver_roster = []
    for b in buses:
        driver_roster.append({
            "driver_name": b.driver_name or "Assigned College Driver",
            "driver_phone": b.driver_phone or "+91 90000 00001",
            "assigned_bus_id": b.bus_id,
            "default_area_id": b.default_area_id,
            "is_active": b.is_active,
            "status": "ACTIVE" if b.is_active else "INACTIVE",
        })

    return {
        "total_drivers": len(driver_roster),
        "drivers": driver_roster,
    }


@router.get("/buses", response_model=list[BusSchema])
def list_fleet(
    area_id: Optional[str] = Query(None, description="Filter fleet by default area"),
    is_active: Optional[bool] = Query(None, description="Filter fleet by active status"),
    search: Optional[str] = Query(None, description="Search bus code, registration, or driver"),
    db: Session = Depends(get_db)
):
    """Retrieves transit buses in the college fleet with driver and corridor info."""
    query = db.query(Bus)
    if area_id is not None:
        _validate_area_id(area_id)
        query = query.filter(Bus.default_area_id == area_id)
    if is_active is not None:
        query = query.filter(Bus.is_active == is_active)
    if search:
        pat = f"%{search.strip().lower()}%"
        query = query.filter(
            func.lower(Bus.bus_id).like(pat) |
            func.lower(Bus.registration_no).like(pat) |
            func.lower(Bus.driver_name).like(pat)
        )
    buses = query.order_by(Bus.bus_id).all()
    return [b.to_dict() for b in buses]


@router.post("/buses", response_model=BusSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def add_bus(payload: BusCreateRequest, db: Session = Depends(get_db)):
    """Registers a new bus into the college fleet."""
    bus_id = payload.bus_id.strip().upper()
    if not bus_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Bus ID cannot be empty."
        )

    existing = db.query(Bus).filter(Bus.bus_id == bus_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bus with ID '{bus_id}' already exists."
        )

    # Validate seats bounds
    if payload.seats < 10 or payload.seats > 120:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Seating capacity must be between 10 and 120 seats."
        )

    default_area_id = _validate_area_id(payload.default_area_id)

    # Prevent conflicting driver assignment across active vehicles
    driver_name = (payload.driver_name or "Assigned College Driver").strip()
    is_bus_active = payload.is_active is not False

    if is_bus_active and driver_name and driver_name.lower() != "assigned college driver":
        conflict_bus = db.query(Bus).filter(
            Bus.is_active == True,
            func.lower(Bus.driver_name) == driver_name.lower()
        ).first()
        if conflict_bus:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Conflicting driver assignment: Driver '{driver_name}' is already assigned to active bus '{conflict_bus.bus_id}'. A driver cannot be assigned to multiple simultaneous vehicles."
            )

    new_bus = Bus(
        bus_id=bus_id,
        seats=payload.seats,
        default_area_id=default_area_id,
        is_active=payload.is_active,
        registration_no=payload.registration_no or f"TN 47 B {bus_id.replace('BUS-', '')}026",
        driver_name=driver_name,
        driver_phone=payload.driver_phone or "+91 90000 00001",
        depot_location=payload.depot_location or "VSB Campus Depot, Karudayampalayam",
        route_name=payload.route_name or f"{default_area_id or 'Zone A'} Kovai Road Radial",
    )
    db.add(new_bus)
    db.commit()
    db.refresh(new_bus)
    return new_bus.to_dict()


@router.put("/buses/{bus_id}", response_model=BusSchema, dependencies=[Depends(require_admin)])
def update_bus(bus_id: str, payload: BusUpdateRequest, db: Session = Depends(get_db)):
    """Updates specifications, capacity, driver, or route for an existing bus."""
    bus = db.query(Bus).filter(Bus.bus_id == bus_id).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bus '{bus_id}' not found."
        )

    if payload.seats is not None:
        if payload.seats < 10 or payload.seats > 120:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Seating capacity must be between 10 and 120 seats."
            )
        bus.seats = payload.seats

    if payload.default_area_id is not None:
        bus.default_area_id = _validate_area_id(payload.default_area_id)

    target_active = payload.is_active if payload.is_active is not None else bus.is_active
    target_driver = (payload.driver_name if payload.driver_name is not None else bus.driver_name or "").strip()

    # Prevent conflicting driver assignment across active vehicles
    if target_active and target_driver and target_driver.lower() != "assigned college driver":
        conflict_bus = db.query(Bus).filter(
            Bus.bus_id != bus_id,
            Bus.is_active == True,
            func.lower(Bus.driver_name) == target_driver.lower()
        ).first()
        if conflict_bus:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Conflicting driver assignment: Driver '{target_driver}' is already assigned to active bus '{conflict_bus.bus_id}'. A driver cannot be assigned to multiple simultaneous vehicles."
            )

    if payload.is_active is not None:
        bus.is_active = payload.is_active
    if payload.registration_no is not None:
        bus.registration_no = payload.registration_no
    if payload.driver_name is not None:
        bus.driver_name = target_driver
    if payload.driver_phone is not None:
        bus.driver_phone = payload.driver_phone
    if payload.depot_location is not None:
        bus.depot_location = payload.depot_location
    if payload.route_name is not None:
        bus.route_name = payload.route_name

    db.commit()
    db.refresh(bus)
    return bus.to_dict()


@router.delete("/buses/{bus_id}", dependencies=[Depends(require_admin)])
def delete_bus(bus_id: str, db: Session = Depends(get_db)):
    """
    Removes or retires a bus from the college fleet.
    Safeguards dispatch integrity: rejects deletion if the bus is referenced
    in existing approved dispatch plans.
    """
    bus = db.query(Bus).filter(Bus.bus_id == bus_id).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bus '{bus_id}' not found."
        )

    # Check for existing plan references
    plan_count = db.query(Plan).filter(Plan.bus_id == bus_id).count()
    if plan_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot delete bus '{bus_id}' because it is assigned in {plan_count} "
                f"approved dispatch plan(s). Deactivate the vehicle instead (set is_active=False) "
                f"to preserve historical dispatch integrity and audit trail."
            )
        )

    db.delete(bus)
    db.commit()
    return {"success": True, "message": f"Bus '{bus_id}' successfully removed from fleet."}
