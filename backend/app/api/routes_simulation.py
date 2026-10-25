from fastapi import APIRouter
from backend.app.schemas import SimulateRequest
from backend.app.core.simulation.simulator import simulator

router = APIRouter(tags=["Transit Simulation"])

@router.post("/simulate")
def run_simulation(req: SimulateRequest = SimulateRequest()):
    """
    Executes backtesting simulation benchmark comparing status-quo fixed allocation
    against BUSify's demand-aware dynamic allocation over recent historical operating days.
    """
    result = simulator.simulate_date_range(sample_days=req.sample_days)
    return result
