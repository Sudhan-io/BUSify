from sqlalchemy import Column, String, Integer, Boolean
from backend.app.database import Base

class Bus(Base):
    """Transit vehicle fleet specifications."""
    __tablename__ = "buses"

    bus_id = Column(String(32), primary_key=True, index=True)
    seats = Column(Integer, default=55, nullable=False)
    default_area_id = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True)
    registration_no = Column(String(32), nullable=True)
    driver_name = Column(String(64), nullable=True)
    driver_phone = Column(String(32), nullable=True)
    depot_location = Column(String(128), nullable=True)
    route_name = Column(String(128), nullable=True)

    def to_dict(self):
        return {
            "bus_id": self.bus_id,
            "seats": self.seats,
            "default_area_id": self.default_area_id,
            "is_active": self.is_active,
            "registration_no": getattr(self, "registration_no", None) or f"TN 47 B {self.bus_id.replace('BUS-', '')}024",
            "driver_name": getattr(self, "driver_name", None) or "Assigned College Driver",
            "driver_phone": getattr(self, "driver_phone", None) or "+91 90000 00001",
            "depot_location": getattr(self, "depot_location", None) or "VSB Campus Depot, Karudayampalayam",
            "route_name": getattr(self, "route_name", None) or f"{self.default_area_id or 'Zone A'} Kovai Road Radial",
        }
