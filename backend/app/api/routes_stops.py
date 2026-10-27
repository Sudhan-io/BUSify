from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models.stop import Stop
from backend.app.models.registration import Registration
from backend.app.schemas import StopSchema, StopCreateRequest, StopUpdateRequest
from backend.app.auth.auth_service import require_admin
from backend.app.core.data.synthetic_generator import AREAS_CONFIG

router = APIRouter(tags=["Transit Stops"])

def _validate_area(area_id: str):
    if area_id not in AREAS_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown area_id '{area_id}'. Valid areas: {sorted(AREAS_CONFIG.keys())}",
        )

@router.get("/stops", response_model=list[StopSchema])
def list_all_stops(
    area_id: Optional[str] = Query(None, description="Filter stops by transit corridor area"),
    db: Session = Depends(get_db)
):
    """Retrieves designated campus bus stops with geocoordinates and authoritative registration counts."""
    query = db.query(Stop)
    if area_id is not None:
        _validate_area(area_id)
        query = query.filter(Stop.area_id == area_id)
    stops = query.order_by(Stop.area_id, Stop.sequence_order).all()

    # Query authoritative student registration volume per stop
    counts_by_stop = dict(
        db.query(Registration.stop_id, func.count(Registration.reg_id))
        .group_by(Registration.stop_id)
        .all()
    )
    result = []
    for s in stops:
        d = s.to_dict()
        d["student_count"] = counts_by_stop.get(s.stop_id, 0)
        result.append(d)
    return result

@router.post("/stops", response_model=StopSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def add_stop(payload: StopCreateRequest, db: Session = Depends(get_db)):
    """Registers a new transit stop along a corridor."""
    existing = db.query(Stop).filter(Stop.stop_id == payload.stop_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stop with ID '{payload.stop_id}' already exists."
        )
    _validate_area(payload.area_id)

    new_stop = Stop(
        stop_id=payload.stop_id,
        name=payload.name,
        lat=payload.lat,
        lon=payload.lon,
        area_id=payload.area_id,
        sequence_order=payload.sequence_order,
    )
    db.add(new_stop)
    db.commit()
    db.refresh(new_stop)
    return new_stop.to_dict()

@router.put("/stops/{stop_id}", response_model=StopSchema, dependencies=[Depends(require_admin)])
def update_stop(stop_id: str, payload: StopUpdateRequest, db: Session = Depends(get_db)):
    """Updates coordinates, corridor zone, or sequence order for a stop."""
    stop = db.query(Stop).filter(Stop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stop with ID '{stop_id}' not found."
        )

    if payload.area_id is not None:
        _validate_area(payload.area_id)
        stop.area_id = payload.area_id
    if payload.name is not None:
        stop.name = payload.name
    if payload.lat is not None:
        stop.lat = payload.lat
    if payload.lon is not None:
        stop.lon = payload.lon
    if payload.sequence_order is not None:
        stop.sequence_order = payload.sequence_order

    db.commit()
    db.refresh(stop)
    return stop.to_dict()

@router.delete("/stops/{stop_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
def delete_stop(stop_id: str, db: Session = Depends(get_db)):
    """Decommission an existing transit stop."""
    stop = db.query(Stop).filter(Stop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stop with ID '{stop_id}' not found."
        )
    db.delete(stop)
    db.commit()
    return {"message": f"Stop '{stop_id}' removed successfully.", "stop_id": stop_id}
