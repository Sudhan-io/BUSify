from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.auth.auth_service import require_admin
from backend.app.database import get_db
from backend.app.models.institution import Institution, seed_default_institutions

router = APIRouter(prefix="/institutions", tags=["Multi-Institution & Campus Scalability"])

class CorridorDefinition(BaseModel):
    id: str
    name: str
    bearing_deg: float

class InstitutionCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128, description="College or University Name")
    campus_code: Optional[str] = Field(None, max_length=32, description="Short code e.g. VSBEC")
    city: str = Field(..., min_length=2, max_length=64, description="Campus City or Town")
    district: str = Field(default="Karur", max_length=64, description="Administrative District")
    state: str = Field(default="Tamil Nadu", max_length=64, description="State")
    campus_lat: float = Field(..., ge=-90.0, le=90.0, description="Campus Gate / Fleet Depot Latitude")
    campus_lng: float = Field(..., ge=-180.0, le=180.0, description="Campus Gate / Fleet Depot Longitude")
    depot_address: Optional[str] = Field(None, max_length=256, description="Physical street or campus address")
    total_fleet_size: int = Field(default=45, ge=1, le=500, description="Number of buses in college fleet")
    default_capacity: int = Field(default=55, ge=10, le=100, description="Seats per bus")

class SetActiveInstitutionRequest(BaseModel):
    institution_id: str

@router.get("/districts")
def list_districts(db: Session = Depends(get_db)):
    """Returns the list of unique districts represented in the database."""
    seed_default_institutions(db)
    district_rows = db.query(Institution.district).filter(Institution.district.isnot(None)).distinct().all()
    districts = sorted(list(set(row[0] for row in district_rows if row[0])))
    if not districts:
        districts = ["Karur"]
    return {
        "districts": ["All Districts"] + districts,
        "total_districts": len(districts)
    }

@router.get("")
def list_institutions(
    district: Optional[str] = Query(default=None, description="Filter by administrative district"),
    search: Optional[str] = Query(default=None, description="Search by college name, code, or city"),
    db: Session = Depends(get_db)
):
    """
    Returns registered college transit networks from database with support for
    district filtering and text search. Resolves SEC-001 by persisting state.
    """
    seed_default_institutions(db)
    query = db.query(Institution)

    if district and district != "All Districts":
        query = query.filter(func.lower(Institution.district) == district.strip().lower())

    if search and search.strip():
        q = f"%{search.strip().lower()}%"
        query = query.filter(
            func.lower(Institution.name).like(q)
            | func.lower(Institution.campus_code).like(q)
            | func.lower(Institution.city).like(q)
            | func.lower(Institution.district).like(q)
        )

    records = query.all()
    institutions = [inst.to_dict() for inst in records]
    return {
        "total_institutions": len(institutions),
        "institutions": institutions
    }

@router.get("/active")
def get_active_institution(db: Session = Depends(get_db)):
    """Returns the currently active college campus profile from database."""
    seed_default_institutions(db)
    active = db.query(Institution).filter(Institution.is_active == True).first()
    if not active:
        active = db.query(Institution).first()
    if not active:
        active = seed_default_institutions(db)
    return active.to_dict()

@router.post("/active", dependencies=[Depends(require_admin)])
def set_active_institution(payload: SetActiveInstitutionRequest, db: Session = Depends(get_db)):
    """Switches the active college across the platform in persistent DB storage."""
    seed_default_institutions(db)
    target = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"Institution '{payload.institution_id}' not found.")

    try:
        # Set all inactive, then activate target
        db.query(Institution).update({Institution.is_active: False})
        target.is_active = True
        db.commit()
        db.refresh(target)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update active institution: {str(err)}")

    return {
        "success": True,
        "message": f"Activated campus: {target.name} ({target.city})",
        "active_institution": target.to_dict()
    }

@router.post("", dependencies=[Depends(require_admin)])
def create_institution(payload: InstitutionCreateRequest, db: Session = Depends(get_db)):
    """
    Registers a new college or university campus and persists it to the institutions table.
    Dynamically initializes transit depot coordinates and corridor geometries.
    """
    seed_default_institutions(db)
    slug_base = "".join(c for c in payload.name if c.isalnum()).upper()[:12]
    count = db.query(Institution).count()
    new_id = f"INST_{slug_base}_{count+1:02d}"

    # Handle ID collision safely
    suffix = 1
    while db.query(Institution).filter(Institution.id == new_id).first():
        new_id = f"INST_{slug_base}_{count+1:02d}_{suffix}"
        suffix += 1

    corridors = [
        {"id": "AREA_A", "name": f"{payload.city} North Corridor", "bearing_deg": 25.0},
        {"id": "AREA_B", "name": f"{payload.city} East Arterial", "bearing_deg": 95.0},
        {"id": "AREA_C", "name": f"{payload.city} South Highway", "bearing_deg": 180.0},
        {"id": "AREA_D", "name": f"{payload.city} West Express", "bearing_deg": 270.0},
        {"id": "AREA_E", "name": f"{payload.city} Central Urban Hub", "bearing_deg": 320.0},
    ]

    try:
        # Deactivate previous active institutions
        db.query(Institution).update({Institution.is_active: False})

        new_inst = Institution(
            id=new_id,
            name=payload.name.strip(),
            campus_code=(payload.campus_code or slug_base[:6]).strip(),
            city=payload.city.strip(),
            district=(payload.district or payload.city).strip(),
            state=payload.state.strip(),
            campus_lat=payload.campus_lat,
            campus_lng=payload.campus_lng,
            depot_address=(payload.depot_address or f"{payload.name} Main Gate Depot, {payload.city}").strip(),
            total_fleet_size=payload.total_fleet_size,
            default_capacity=payload.default_capacity,
            is_active=True,
            corridors=corridors
        )
        db.add(new_inst)
        db.commit()
        db.refresh(new_inst)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error registering institution: {str(err)}")

    return {
        "success": True,
        "message": f"Successfully registered and activated campus: {new_inst.name}",
        "institution": new_inst.to_dict()
    }
