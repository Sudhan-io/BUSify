from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, text
from datetime import datetime, timezone
from backend.app.database import Base, engine

class Plan(Base):
    """Daily optimized bus allocation and route sequence plan."""
    __tablename__ = "plans"

    plan_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), index=True, nullable=False)
    slot = Column(String(16), default="morning", nullable=False)
    bus_id = Column(String(32), ForeignKey("buses.bus_id"), nullable=False)
    area_id = Column(String(32), nullable=False)
    scenario = Column(String(32), default="REGULAR", nullable=True)
    status = Column(String(32), default="APPROVED", nullable=True)
    total_riders = Column(Integer, default=0, nullable=True)
    route_json = Column(Text, nullable=False)  # JSON-encoded ordered stops and times
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "plan_id": self.plan_id,
            "date": self.date,
            "slot": self.slot,
            "bus_id": self.bus_id,
            "area_id": self.area_id,
            "scenario": getattr(self, "scenario", None) or "REGULAR",
            "status": getattr(self, "status", None) or "APPROVED",
            "total_riders": getattr(self, "total_riders", 0) or 0,
            "route_json": self.route_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

def ensure_plan_columns():
    """Ensure optional plan management columns exist in SQLite database (Resolves M-13 / H-21)."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(plans)")).fetchall()
            existing_cols = {row[1] for row in result}
            new_cols = [
                ("scenario", "TEXT DEFAULT 'REGULAR'"),
                ("status", "TEXT DEFAULT 'APPROVED'"),
                ("total_riders", "INTEGER DEFAULT 0"),
            ]
            for col_name, col_def in new_cols:
                if col_name not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE plans ADD COLUMN {col_name} {col_def}"))
                        conn.commit()
                    except Exception:
                        pass
    except Exception as e:
        print(f"Plan column migration notice: {e}")

_ensure_plan_columns = ensure_plan_columns
