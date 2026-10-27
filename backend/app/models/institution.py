from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Float, Integer, Boolean, JSON
from sqlalchemy.orm import Session
from backend.app.database import Base
from backend.app.config import settings

class Institution(Base):
    """
    Persistent college or university transit network profile.
    Resolves SEC-001 by persisting campus specifications to the database.
    """
    __tablename__ = "institutions"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    campus_code = Column(String(32), nullable=True)
    city = Column(String(64), nullable=False)
    district = Column(String(64), nullable=True, default="Karur")
    state = Column(String(64), nullable=True, default="Tamil Nadu")
    campus_lat = Column(Float, nullable=False)
    campus_lng = Column(Float, nullable=False)
    depot_address = Column(String(256), nullable=True)
    total_fleet_size = Column(Integer, default=45, nullable=False)
    default_capacity = Column(Integer, default=55, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    corridors = Column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes institution entity conforming to API contract."""
        default_corridors = [
            {"id": "AREA_A", "name": f"{self.city} West Corridor (Kovai Road)", "bearing_deg": 270.0},
            {"id": "AREA_B", "name": f"{self.city} South Hub (Gandhigramam)", "bearing_deg": 180.0},
            {"id": "AREA_C", "name": f"{self.city} South-East (Thanthonimalai)", "bearing_deg": 135.0},
            {"id": "AREA_D", "name": f"{self.city} North Corridor (Velur)", "bearing_deg": 0.0},
            {"id": "AREA_E", "name": f"{self.city} North-West (Paramathi)", "bearing_deg": 315.0},
        ]
        return {
            "id": self.id,
            "name": self.name,
            "campus_code": self.campus_code,
            "city": self.city,
            "district": self.district or "Karur",
            "state": self.state or "Tamil Nadu",
            "campus_lat": self.campus_lat,
            "campus_lng": self.campus_lng,
            "depot_address": self.depot_address,
            "total_fleet_size": self.total_fleet_size,
            "default_capacity": self.default_capacity,
            "active": bool(self.is_active),
            "corridors": self.corridors or default_corridors,
        }

DEFAULT_VSB_CORRIDORS = [
    {"id": "AREA_A", "name": "Zone A: Karudayampalayam & Kovai Road (West)", "bearing_deg": 270.0},
    {"id": "AREA_B", "name": "Zone B: Gandhigramam & South Hub (South)", "bearing_deg": 180.0},
    {"id": "AREA_C", "name": "Zone C: Thanthonimalai & South-East", "bearing_deg": 135.0},
    {"id": "AREA_D", "name": "Zone D: Velur & North Corridor (North)", "bearing_deg": 0.0},
    {"id": "AREA_E", "name": "Zone E: Paramathi & West Rural (North-West)", "bearing_deg": 315.0},
]

def seed_default_institutions(db: Session) -> Optional[Institution]:
    """
    Idempotently seeds the default VSB Engineering College institution record.
    Uses canonical campus coordinates from settings.
    """
    has_active = db.query(Institution).filter(Institution.is_active == True).first()
    vsb = db.query(Institution).filter(Institution.id == "VSB_KARUR").first()
    if vsb is None:
        vsb = Institution(
            id="VSB_KARUR",
            name="VSB Engineering College",
            campus_code="VSBEC",
            city="Karudayampalayam, Karur",
            district="Karur",
            state="Tamil Nadu",
            campus_lat=settings.COLLEGE_DEPOT_LAT,  # 10.95488 (M-02 canonical)
            campus_lng=settings.COLLEGE_DEPOT_LON,  # 77.95462 (M-02 canonical)
            depot_address="NH-67 Covai Road, Karudayampalayam, Karur 639111",
            total_fleet_size=45,
            default_capacity=55,
            is_active=not bool(has_active),
            corridors=DEFAULT_VSB_CORRIDORS,
        )
        db.add(vsb)
        db.commit()
        db.refresh(vsb)
    else:
        # Update corridors to canonical if previously set to legacy defaults or empty
        if not vsb.corridors or any("Central & Vengamedu" in str(c) for c in (vsb.corridors or [])):
            vsb.corridors = DEFAULT_VSB_CORRIDORS
            db.commit()
            db.refresh(vsb)
        # Ensure at least one institution is marked active if none is
        if not has_active:
            vsb.is_active = True
            db.commit()
            db.refresh(vsb)
    return vsb
