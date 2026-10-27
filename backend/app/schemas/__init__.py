from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class StopSchema(BaseModel):
    stop_id: str
    name: str
    lat: float
    lon: float
    area_id: str
    sequence_order: int

class StopCreateRequest(BaseModel):
    stop_id: str
    name: str
    lat: float
    lon: float
    area_id: str
    sequence_order: int = 1

class StopUpdateRequest(BaseModel):
    name: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    area_id: Optional[str] = None
    sequence_order: Optional[int] = None

class BusSchema(BaseModel):
    bus_id: str
    seats: int
    default_area_id: Optional[str] = None
    is_active: bool
    registration_no: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    depot_location: Optional[str] = None
    route_name: Optional[str] = None

class BusCreateRequest(BaseModel):
    bus_id: str
    seats: int = Field(default=55, ge=10, le=120, description="Seats per bus (must be positive)")
    default_area_id: Optional[str] = "AREA_A"
    registration_no: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    depot_location: Optional[str] = "VSB Campus Depot, Karudayampalayam"
    route_name: Optional[str] = None
    is_active: bool = True

class BusUpdateRequest(BaseModel):
    seats: Optional[int] = Field(default=None, ge=10, le=120, description="Seats per bus (must be positive)")
    default_area_id: Optional[str] = None
    registration_no: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    depot_location: Optional[str] = None
    route_name: Optional[str] = None
    is_active: Optional[bool] = None

class AreaForecastItem(BaseModel):
    area_id: str
    date: str
    p50_demand: int
    p90_demand: int

class ForecastResponse(BaseModel):
    date: str
    is_exam_day: bool
    areas: List[AreaForecastItem]
    total_p50_demand: int
    total_p90_demand: int

class AllocationResponse(BaseModel):
    date: str
    status: str
    total_fleet_available: int
    total_buses_allocated: int
    baseline_allocation: Dict[str, int]
    optimized_allocation: Dict[str, int]
    metrics: Dict[str, Any]
    per_area_details: Dict[str, Any]

class SimulateRequest(BaseModel):
    sample_days: int = Field(default=7, ge=1, le=30)
