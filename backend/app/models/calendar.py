from sqlalchemy import Column, String, Integer, Boolean
from backend.app.database import Base

class Calendar(Base):
    """Academic calendar dates, exams, and class schedules."""
    __tablename__ = "calendar"

    date = Column(String(10), primary_key=True)  # Format: YYYY-MM-DD
    day_of_week = Column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    is_holiday = Column(Boolean, default=False, nullable=False)
    exam_flag = Column(Boolean, default=False, nullable=False)
    first_class_time = Column(String(8), default="08:30")

    def to_dict(self):
        return {
            "date": self.date,
            "day_of_week": self.day_of_week,
            "is_holiday": self.is_holiday,
            "exam_flag": self.exam_flag,
            "first_class_time": self.first_class_time,
        }
