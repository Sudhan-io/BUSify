from sqlalchemy import Column, Integer, String, ForeignKey
from backend.app.database import Base

class DemandObservation(Base):
    """Historical or logged actual ridership count at a stop."""
    __tablename__ = "demand_obs"

    obs_id = Column(Integer, primary_key=True, autoincrement=True)
    stop_id = Column(String(32), ForeignKey("stops.stop_id"), nullable=False, index=True)
    date = Column(String(10), ForeignKey("calendar.date"), nullable=False, index=True)
    slot = Column(String(16), default="morning", nullable=False)
    riders = Column(Integer, nullable=False)
    source = Column(String(32), default="field_count")  # attendance, field_count, survey

    def to_dict(self):
        return {
            "obs_id": self.obs_id,
            "stop_id": self.stop_id,
            "date": self.date,
            "slot": self.slot,
            "riders": self.riders,
            "source": self.source,
        }
