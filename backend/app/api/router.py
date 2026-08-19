from fastapi import APIRouter

from app.api.routes import audit, auth, health, inventory, investigations, knowledge

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(audit.router)
api_router.include_router(inventory.router)
api_router.include_router(knowledge.router)
api_router.include_router(investigations.router)
