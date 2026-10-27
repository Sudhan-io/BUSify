from sqlalchemy import Column, String, Float, Integer
from backend.app.database import Base

class Stop(Base):
    """Bus stop location and regional zone grouping."""
    __tablename__ = "stops"

    stop_id = Column(String(32), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    area_id = Column(String(32), nullable=False, index=True)
    sequence_order = Column(Integer, default=0)

    def to_dict(self, student_count: int = 0):
        return {
            "stop_id": self.stop_id,
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
            "area_id": self.area_id,
            "sequence_order": self.sequence_order,
            "student_count": getattr(self, "student_count", student_count),
        }
