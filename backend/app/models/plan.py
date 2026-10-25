from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime
from backend.app.database import Base

class Plan(Base):
    """Daily optimized bus allocation and route sequence plan."""
    __tablename__ = "plans"

    plan_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), index=True, nullable=False)
    slot = Column(String(16), default="morning", nullable=False)
    bus_id = Column(String(32), ForeignKey("buses.bus_id"), nullable=False)
    area_id = Column(String(32), nullable=False)
    route_json = Column(Text, nullable=False)  # JSON-encoded ordered stops and times
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "plan_id": self.plan_id,
            "date": self.date,
            "slot": self.slot,
            "bus_id": self.bus_id,
            "area_id": self.area_id,
            "route_json": self.route_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
