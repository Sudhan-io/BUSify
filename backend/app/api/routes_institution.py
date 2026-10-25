from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from pydantic import BaseModel, Field

from backend.app.auth.auth_service import require_admin

router = APIRouter(prefix="/institutions", tags=["Multi-Institution & Campus Scalability"])

class CorridorDefinition(BaseModel):
    id: str
    name: str
    bearing_deg: float

class InstitutionCreateRequest(BaseModel):
    name: str = Field(..., description="College or University Name")
    campus_code: Optional[str] = Field(None, description="Short code e.g. VSBEC")
    city: str = Field(..., description="Campus City or Town")
    district: str = Field(default="Karur", description="Administrative District")
    state: str = Field(default="Tamil Nadu", description="State")
    campus_lat: float = Field(..., description="Campus Gate / Fleet Depot Latitude")
    campus_lng: float = Field(..., description="Campus Gate / Fleet Depot Longitude")
    depot_address: Optional[str] = Field(None, description="Physical street or campus address")
    total_fleet_size: int = Field(default=45, ge=1, le=500, description="Number of buses in college fleet")
    default_capacity: int = Field(default=55, ge=10, le=100, description="Seats per bus")

class SetActiveInstitutionRequest(BaseModel):
    institution_id: str

# In-memory registry with VSB Engineering College, Karur as the primary institution
INSTITUTIONS_REGISTRY = [
    {
        "id": "VSB_KARUR",
        "name": "VSB Engineering College",
        "campus_code": "VSBEC",
        "city": "Karudayampalayam, Karur",
        "district": "Karur",
        "state": "Tamil Nadu",
        "campus_lat": 10.95488,
        "campus_lng": 77.95462,
        "depot_address": "NH-67 Covai Road, Karudayampalayam, Karur 639111",
        "total_fleet_size": 45,
        "default_capacity": 55,
        "active": True,
        "corridors": [
            {"id": "AREA_A", "name": "Zone A: Central & Vengamedu (Kovai Road)", "bearing_deg": 15.0},
            {"id": "AREA_B", "name": "Zone B: Gandhigramam & South Hub (Thanthonimalai)", "bearing_deg": 95.0},
            {"id": "AREA_C", "name": "Zone C: Pasupathipalayam & East (Amaravathi)", "bearing_deg": 180.0},
            {"id": "AREA_D", "name": "Zone D: Sanapiratti & North Radial", "bearing_deg": 270.0},
            {"id": "AREA_E", "name": "Zone E: Inam Karur & Urban Core", "bearing_deg": 320.0},
        ]
    }
]

@router.get("/districts")
def list_districts():
    """Returns the list of unique districts represented in the system."""
    districts = sorted(list(set(inst.get("district", "Karur") for inst in INSTITUTIONS_REGISTRY)))
    return {
        "districts": ["All Districts"] + districts,
        "total_districts": len(districts)
    }

@router.get("")
def list_institutions(
    district: Optional[str] = Query(default=None, description="Filter by administrative district"),
    search: Optional[str] = Query(default=None, description="Search by college name, code, or city")
):
    """
    Returns registered college transit networks with support for district filtering and text search.
    """
    filtered = INSTITUTIONS_REGISTRY

    if district and district != "All Districts":
        filtered = [inst for inst in filtered if inst.get("district", "").lower() == district.lower()]

    if search and search.strip():
        q = search.strip().lower()
        filtered = [
            inst for inst in filtered
            if q in inst["name"].lower()
            or q in inst.get("campus_code", "").lower()
            or q in inst.get("city", "").lower()
            or q in inst.get("district", "").lower()
        ]

    return {
        "total_institutions": len(filtered),
        "institutions": filtered
    }

@router.get("/active")
def get_active_institution():
    """Returns the currently active college campus profile."""
    active = next((inst for inst in INSTITUTIONS_REGISTRY if inst.get("active")), INSTITUTIONS_REGISTRY[0])
    return active

@router.post("/active", dependencies=[Depends(require_admin)])
def set_active_institution(payload: SetActiveInstitutionRequest):
    """Switches the active college across the platform."""
    found = False
    for inst in INSTITUTIONS_REGISTRY:
        if inst["id"] == payload.institution_id:
            inst["active"] = True
            found = True
        else:
            inst["active"] = False
            
    if not found:
        raise HTTPException(status_code=404, detail=f"Institution '{payload.institution_id}' not found.")
        
    active = next(inst for inst in INSTITUTIONS_REGISTRY if inst.get("active"))
    return {
        "success": True,
        "message": f"Activated campus: {active['name']} ({active['city']})",
        "active_institution": active
    }

@router.post("", dependencies=[Depends(require_admin)])
def create_institution(payload: InstitutionCreateRequest):
    """
    Registers a new college or university campus to scale BUSify to any institution.
    Dynamically initializes transit depot coordinates and corridor geometries.
    """
    slug_base = "".join(c for c in payload.name if c.isalnum()).upper()[:12]
    new_id = f"INST_{slug_base}_{len(INSTITUTIONS_REGISTRY)+1:02d}"
    
    corridors = [
        {"id": "AREA_A", "name": f"{payload.city} North Corridor", "bearing_deg": 25.0},
        {"id": "AREA_B", "name": f"{payload.city} East Arterial", "bearing_deg": 95.0},
        {"id": "AREA_C", "name": f"{payload.city} South Highway", "bearing_deg": 180.0},
        {"id": "AREA_D", "name": f"{payload.city} West Express", "bearing_deg": 270.0},
        {"id": "AREA_E", "name": f"{payload.city} Central Urban Hub", "bearing_deg": 320.0},
    ]
    
    for inst in INSTITUTIONS_REGISTRY:
        inst["active"] = False
        
    new_inst = {
        "id": new_id,
        "name": payload.name,
        "campus_code": payload.campus_code or slug_base[:6],
        "city": payload.city,
        "district": payload.district or payload.city,
        "state": payload.state,
        "campus_lat": payload.campus_lat,
        "campus_lng": payload.campus_lng,
        "depot_address": payload.depot_address or f"{payload.name} Main Gate Depot, {payload.city}",
        "total_fleet_size": payload.total_fleet_size,
        "default_capacity": payload.default_capacity,
        "active": True,
        "corridors": corridors
    }
    
    INSTITUTIONS_REGISTRY.append(new_inst)
    
    return {
        "success": True,
        "message": f"Successfully registered and activated campus: {new_inst['name']}",
        "institution": new_inst
    }
