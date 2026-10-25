from fastapi import APIRouter
from backend.app.api.routes_stops import router as stops_router
from backend.app.api.routes_buses import router as buses_router
from backend.app.api.routes_forecast import router as forecast_router
from backend.app.api.routes_allocation import router as allocation_router
from backend.app.api.routes_routing import router as routing_router
from backend.app.api.routes_crowding import router as crowding_router
from backend.app.api.routes_simulation import router as simulation_router
from backend.app.api.routes_workflow import router as workflow_router
from backend.app.api.routes_institution import router as institutions_router

api_router = APIRouter()

api_router.include_router(stops_router)
api_router.include_router(buses_router)
api_router.include_router(forecast_router)
api_router.include_router(allocation_router)
api_router.include_router(routing_router)
api_router.include_router(crowding_router)
api_router.include_router(simulation_router)
api_router.include_router(workflow_router)
api_router.include_router(institutions_router)
