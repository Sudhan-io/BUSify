import os
import json
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.models.stop import Stop
from backend.app.models.bus import Bus
from backend.app.models.registration import Registration
from backend.app.models.calendar import Calendar
from backend.app.models.demand import DemandObservation
from backend.app.core.data.anonymizer import hash_student_id

# Seed for deterministic reproducibility
random.seed(42)
np.random.seed(42)

# College Depot Coordinate
DEPOT_LAT = settings.COLLEGE_DEPOT_LAT
DEPOT_LON = settings.COLLEGE_DEPOT_LON

AREAS_CONFIG = {
    "AREA_A": {
        "name": "Karudayampalayam & Kovai Road",
        "baseline_buses": 10,
        "stops": [
            ("ST-A01", "Karudayampalayam Bus Stop", 10.9592, 77.9482, 0.16),
            ("ST-A02", "VSB College Gate Arch", 10.9548, 77.9546, 0.15),
            ("ST-A03", "Kovai Road Arch Checkpost", 10.9620, 77.9710, 0.12),
            ("ST-A04", "Central Bus Stand (Karur)", 10.9575, 78.0815, 0.11),
            ("ST-A05", "Vengamedu Junction", 10.9690, 78.0790, 0.10),
            ("ST-A06", "Textile City Gate", 10.9750, 78.0750, 0.09),
            ("ST-A07", "Light House Corner", 10.9540, 78.0860, 0.08),
            ("ST-A08", "Ramakrishnapuram", 10.9660, 78.0850, 0.07),
            ("ST-A09", "Railway Colony", 10.9510, 78.0770, 0.06),
            ("ST-A10", "Anna Nagar Corner", 10.9710, 78.0820, 0.06),
        ]
    },
    "AREA_B": {
        "name": "Gandhigramam & South Hub",
        "baseline_buses": 12,
        "stops": [
            ("ST-B01", "Gandhigramam South", 10.9380, 78.0750, 0.16),
            ("ST-B02", "Sanapiratti Roundabout", 10.9420, 78.0880, 0.14),
            ("ST-B03", "Government Hospital Gate", 10.9490, 78.0790, 0.12),
            ("ST-B04", "Thirumanilaiyur", 10.9320, 78.0830, 0.11),
            ("ST-B05", "Rayanoor Junction", 10.9250, 78.0690, 0.10),
            ("ST-B06", "Vennamalai Bypass", 10.9450, 78.0660, 0.08),
            ("ST-B07", "Kalyana Venkataramana Temple", 10.9360, 78.0610, 0.08),
            ("ST-B08", "Andankoil East", 10.9290, 78.0930, 0.07),
            ("ST-B09", "Five Roads Crossing", 10.9400, 78.0810, 0.06),
            ("ST-B10", "Co-Op Colony", 10.9210, 78.0780, 0.04),
            ("ST-B11", "South By-Pass Toll", 10.9150, 78.0850, 0.04),
        ]
    },
    "AREA_C": {
        "name": "Thanthonimalai & South-East",
        "baseline_buses": 8,
        "stops": [
            ("ST-C01", "Thanthonimalai Hill Gate", 10.9280, 78.0990, 0.18),
            ("ST-C02", "Arts College Entrance", 10.9220, 78.1050, 0.16),
            ("ST-C03", "Collectorate Complex", 10.9340, 78.0950, 0.15),
            ("ST-C04", "Sungagate", 10.9410, 78.0970, 0.14),
            ("ST-C05", "Kalingarayan Canal Stop", 10.9160, 78.1120, 0.11),
            ("ST-C06", "Velliyanai Road Branch", 10.9080, 78.1180, 0.10),
            ("ST-C07", "Muthuraja Nagar", 10.9300, 78.1080, 0.08),
            ("ST-C08", "Chinnandankoil", 10.9380, 78.1030, 0.08),
        ]
    },
    "AREA_D": {
        "name": "Velur & North Corridor",
        "baseline_buses": 12,
        "stops": [
            ("ST-D01", "Velur Bridge Checkpost", 11.0020, 78.0620, 0.16),
            ("ST-D02", "Kaundampalayam", 10.9930, 78.0670, 0.14),
            ("ST-D03", "Manmangalam High School", 10.9850, 78.0720, 0.13),
            ("ST-D04", "Vangal Ferry Road", 11.0110, 78.0580, 0.11),
            ("ST-D05", "Nerur Temple Branch", 10.9980, 78.0480, 0.10),
            ("ST-D06", "Thalavapalayam College Stop", 11.0190, 78.0520, 0.09),
            ("ST-D07", "Pugalur Sugar Factory Gate", 11.0320, 78.0420, 0.09),
            ("ST-D08", "TNPL Paper Mills Colony", 11.0410, 78.0350, 0.08),
            ("ST-D09", "Kattur Pirivu", 10.9780, 78.0690, 0.06),
            ("ST-D10", "Kuppuchipalayam", 10.9890, 78.0590, 0.04),
        ]
    },
    "AREA_E": {
        "name": "Paramathi & West Rural",
        "baseline_buses": 8,
        "stops": [
            ("ST-E01", "Paramathi Velur Four Roads", 11.0250, 78.0120, 0.18),
            ("ST-E02", "Kabilarmalai Arch", 11.0390, 77.9980, 0.16),
            ("ST-E03", "Jedarpalayam Dam Road", 11.0520, 77.9820, 0.14),
            ("ST-E04", "Noyyal River Junction", 11.0080, 77.9650, 0.13),
            ("ST-E05", "Pondurai Branch", 10.9950, 77.9890, 0.11),
            ("ST-E06", "Aravakurichi Outer", 10.9820, 78.0150, 0.10),
            ("ST-E07", "Pallapatti Market Gate", 10.9710, 78.0300, 0.10),
            ("ST-E08", "Chinnadharapuram Bus Stand", 10.9610, 77.9550, 0.08),
        ]
    }
}

TOTAL_STUDENTS = 2200

def initialize_database():
    """Drops existing tables and recreates clean schemas."""
    Base.metadata.create_all(bind=engine)

def seed_stops(db):
    """Inserts all designated transit stops."""
    created_stops = []
    for area_id, config in AREAS_CONFIG.items():
        for seq, (stop_id, name, lat, lon, weight) in enumerate(config["stops"], start=1):
            stop = Stop(
                stop_id=stop_id,
                name=name,
                lat=lat,
                lon=lon,
                area_id=area_id,
                sequence_order=seq
            )
            db.add(stop)
            created_stops.append(stop)
    db.commit()
    return created_stops

def seed_buses(db):
    """Inserts the 50 bus fleet with baseline area allocations."""
    buses = []
    bus_counter = 1
    for area_id, config in AREAS_CONFIG.items():
        count = config["baseline_buses"]
        for _ in range(count):
            bus_id = f"BUS-{bus_counter:02d}"
            bus = Bus(
                bus_id=bus_id,
                seats=settings.DEFAULT_BUS_CAPACITY,
                default_area_id=area_id,
                is_active=True
            )
            db.add(bus)
            buses.append(bus)
            bus_counter += 1
    db.commit()
    return buses

def seed_registrations(db):
    """Generates 2,200 anonymized student registrations distributed across stops."""
    registrations = []
    all_stops = []
    stop_weights = []

    for area_id, config in AREAS_CONFIG.items():
        area_share = config["baseline_buses"] / settings.TOTAL_FLEET_SIZE
        for stop_id, name, lat, lon, weight in config["stops"]:
            all_stops.append(stop_id)
            stop_weights.append(weight * area_share)

    # Normalize weights
    stop_weights = np.array(stop_weights) / np.sum(stop_weights)

    assigned_stops = np.random.choice(all_stops, size=TOTAL_STUDENTS, p=stop_weights)

    for i in range(1, TOTAL_STUDENTS + 1):
        raw_student_id = f"2023-CS-{i:04d}" if i <= 1000 else f"2024-EC-{i:04d}"
        s_hash = hash_student_id(raw_student_id)
        reg = Registration(
            student_hash=s_hash,
            stop_id=assigned_stops[i - 1],
            academic_year="2025-2026"
        )
        db.add(reg)
        registrations.append(reg)
    
    db.commit()
    return registrations

def seed_calendar_and_demand(db, days_back=90, days_forward=14):
    """
    Generates academic calendar dates and historical observed ridership
    modeling weekday patterns, exam surges, and random weather/attendance fluctuations.
    """
    today = datetime.now().date()
    start_date = today - timedelta(days=days_back)
    end_date = today + timedelta(days=days_forward)

    # Query registration counts per stop
    reg_df = pd.read_sql(
        "SELECT stop_id, COUNT(*) as reg_count FROM registrations GROUP BY stop_id",
        con=engine
    )
    reg_dict = dict(zip(reg_df["stop_id"], reg_df["reg_count"]))

    current_d = start_date
    calendar_entries = []
    demand_entries = []

    # Choose specific dates for mid-term exams in historical data
    exam_week_1_start = today - timedelta(days=50)
    exam_week_1_end = exam_week_1_start + timedelta(days=5)
    
    exam_week_2_start = today - timedelta(days=15)
    exam_week_2_end = exam_week_2_start + timedelta(days=5)

    while current_d <= end_date:
        d_str = current_d.strftime("%Y-%m-%d")
        dow = current_d.weekday()  # 0=Mon, ..., 6=Sun
        is_weekend = dow >= 5
        is_holiday = is_weekend or (dow == 4 and current_d.day == 15)  # Occasional festival
        is_exam = False

        if not is_holiday:
            if (exam_week_1_start <= current_d <= exam_week_1_end) or \
               (exam_week_2_start <= current_d <= exam_week_2_end):
                is_exam = True

        cal = Calendar(
            date=d_str,
            day_of_week=dow,
            is_holiday=is_holiday,
            exam_flag=is_exam,
            first_class_time="08:30"
        )
        db.add(cal)
        calendar_entries.append(cal)

        # Only generate past demand observations up to today for working days
        if current_d <= today and not is_holiday:
            # Determine base attendance rate
            if is_exam:
                base_rate = np.random.uniform(0.93, 0.98)  # Exam surge
            elif dow == 0:  # Monday peak
                base_rate = np.random.uniform(0.85, 0.92)
            elif dow == 4:  # Friday slight drop
                base_rate = np.random.uniform(0.72, 0.80)
            else:
                base_rate = np.random.uniform(0.78, 0.86)

            for stop_id, registered in reg_dict.items():
                # Add stop-level noise
                stop_noise = np.random.normal(0, 0.05)
                rate = np.clip(base_rate + stop_noise, 0.40, 1.0)
                actual_riders = int(round(registered * rate))

                # Inject occasional localized crowding surge in Area B or Area D
                if "ST-B" in stop_id and np.random.rand() < 0.15:
                    actual_riders = min(registered, int(actual_riders * 1.25))

                demand_entries.append(
                    DemandObservation(
                        stop_id=stop_id,
                        date=d_str,
                        slot="morning",
                        riders=actual_riders,
                        source="field_count"
                    )
                )

        current_d += timedelta(days=1)

    db.bulk_save_objects(demand_entries)
    db.commit()
    return len(calendar_entries), len(demand_entries)

def run_synthetic_seed():
    """Main execution function to bootstrap the database."""
    print("Initializing database tables...")
    initialize_database()

    db = SessionLocal()
    try:
        print("Seeding stops...")
        stops = seed_stops(db)
        print(f"-> Created {len(stops)} stops across 5 areas.")

        print("Seeding fleet...")
        buses = seed_buses(db)
        print(f"-> Created {len(buses)} buses.")

        print("Seeding student registrations...")
        regs = seed_registrations(db)
        print(f"-> Created {len(regs)} anonymized student registrations.")

        print("Seeding academic calendar and historical demand observations...")
        num_cal, num_dem = seed_calendar_and_demand(db)
        print(f"-> Created {num_cal} calendar days and {num_dem} demand records.")

        # Ensure seed output directory exists
        os.makedirs("data/seed", exist_ok=True)
        print("Database seeded successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    run_synthetic_seed()
