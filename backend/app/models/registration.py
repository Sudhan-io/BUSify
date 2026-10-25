from sqlalchemy import Column, Integer, String, ForeignKey
from backend.app.database import Base

class Registration(Base):
    """Anonymized student bus service registration record."""
    __tablename__ = "registrations"

    reg_id = Column(Integer, primary_key=True, autoincrement=True)
    student_hash = Column(String(64), nullable=False, index=True)
    stop_id = Column(String(32), ForeignKey("stops.stop_id"), nullable=False, index=True)
    academic_year = Column(String(16), default="2025-2026")

    def to_dict(self):
        return {
            "reg_id": self.reg_id,
            "student_hash": self.student_hash,
            "stop_id": self.stop_id,
            "academic_year": self.academic_year,
        }
