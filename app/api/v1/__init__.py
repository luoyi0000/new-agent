from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.books import router as books_router
from app.api.v1.seats import router as seats_router
from app.api.v1.appointments import router as appointments_router
from app.api.v1.chat import router as chat_router
from app.api.v1.policies import router as policies_router
from app.api.v1.memory import router as memory_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(books_router)
api_v1_router.include_router(seats_router)
api_v1_router.include_router(appointments_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(policies_router)
api_v1_router.include_router(memory_router)
