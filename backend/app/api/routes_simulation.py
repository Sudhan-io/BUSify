import threading
from fastapi import APIRouter, HTTPException, status
from backend.app.schemas import SimulateRequest
from backend.app.core.simulation.simulator import simulator

router = APIRouter(tags=["Transit Simulation"])

_simulation_lock = threading.Lock()

@router.post("/simulate")
def run_simulation(req: SimulateRequest = SimulateRequest()):
    """
    Executes backtesting simulation benchmark comparing status-quo fixed allocation
    against BUSify's demand-aware dynamic allocation over recent historical operating days.
    Guarded with concurrency limit to prevent CPU saturation (SEC-003).
    """
    acquired = _simulation_lock.acquire(blocking=False)
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="A transit simulation is already running. Please retry once it finishes."
        )
    try:
        result = simulator.simulate_date_range(sample_days=req.sample_days)
        return result
    finally:
        _simulation_lock.release()
