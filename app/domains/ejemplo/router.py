from fastapi import APIRouter

from app.domains.ejemplo.schemas import EjemploCreate, EjemploResponse
from app.domains.ejemplo.service import crear_ejemplo

router = APIRouter()


@router.post("/", response_model=EjemploResponse, status_code=201)
async def create_ejemplo(data: EjemploCreate):
    return crear_ejemplo(data)
