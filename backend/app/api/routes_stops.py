from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.stop import Stop
from backend.app.schemas import StopSchema

router = APIRouter(tags=["Transit Stops"])

@router.get("/stops", response_model=list[StopSchema])
def list_all_stops(db: Session = Depends(get_db)):
    """Retrieves all designated campus bus stops with geocoordinates."""
    stops = db.query(Stop).order_by(Stop.area_id, Stop.sequence_order).all()
    return [s.to_dict() for s in stops]
