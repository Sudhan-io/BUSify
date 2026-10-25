"""
student_attendance.py — Persistent daily travel preference model.

Replaces the in-memory OPTED_OUT_STUDENTS set which was wiped on every server restart.
Each row records whether a student plans to travel on a specific date.
Unique constraint on (student_roll_hash, travel_date) prevents duplicates.
"""

from sqlalchemy import Column, String, Boolean, Date, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from backend.app.database import Base


class StudentAttendance(Base):
    """
    Persistent daily travel opt-in / opt-out preferences per student per date.

    Schema:
        student_roll_hash  — Anonymised SHA-256 hash of student roll number
        travel_date        — The calendar date this preference applies to (YYYY-MM-DD)
        traveling_today    — True = confirmed traveling, False = opted out / absent
        updated_at         — Automatic timestamp of last update
    """
    __tablename__ = "student_attendance"

    id = Column(String(64), primary_key=True)  # SHA256(roll + date) — deterministic PK
    student_roll_hash = Column(String(64), nullable=False, index=True)
    travel_date = Column(Date, nullable=False, index=True)
    traveling_today = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("student_roll_hash", "travel_date", name="uq_student_date"),
    )

    def to_dict(self) -> dict:
        return {
            "student_roll_hash": self.student_roll_hash,
            "travel_date": str(self.travel_date),
            "traveling_today": self.traveling_today,
            "updated_at": str(self.updated_at),
        }
