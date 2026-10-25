from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database import get_db, engine
from backend.app.models.bus import Bus
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


def _ensure_bus_columns():
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

_ensure_bus_columns()

@router.get("/buses", response_model=list[BusSchema])
def list_fleet(db: Session = Depends(get_db)):
    """Retrieves all transit buses in the college fleet with driver and route info."""
    buses = db.query(Bus).order_by(Bus.bus_id).all()
    return [b.to_dict() for b in buses]

@router.post("/buses", response_model=BusSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def add_bus(payload: BusCreateRequest, db: Session = Depends(get_db)):
    """Registers a new bus into the college fleet."""
    existing = db.query(Bus).filter(Bus.bus_id == payload.bus_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bus with ID '{payload.bus_id}' already exists."
        )

    default_area_id = _validate_area_id(payload.default_area_id)

    new_bus = Bus(
        bus_id=payload.bus_id,
        seats=payload.seats,
        default_area_id=default_area_id,
        is_active=payload.is_active,
        registration_no=payload.registration_no or f"TN 47 B {payload.bus_id.replace('BUS-', '')}026",
        driver_name=payload.driver_name or "Assigned College Driver",
        driver_phone=payload.driver_phone or "+91 98421 10293",
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

    if payload.default_area_id is not None:
        bus.default_area_id = _validate_area_id(payload.default_area_id)
    if payload.seats is not None:
        bus.seats = payload.seats
    if payload.is_active is not None:
        bus.is_active = payload.is_active
    if payload.registration_no is not None:
        bus.registration_no = payload.registration_no
    if payload.driver_name is not None:
        bus.driver_name = payload.driver_name
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
    """Removes or retires a bus from the active college fleet."""
    bus = db.query(Bus).filter(Bus.bus_id == bus_id).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bus '{bus_id}' not found."
        )

    db.delete(bus)
    db.commit()
    return {"success": True, "message": f"Bus '{bus_id}' successfully removed from fleet."}
