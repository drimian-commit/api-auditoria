from fastapi import APIRouter

from app.config import get_settings
from app.domains.ejemplo.schemas import EjemploCreate, EjemploResponse
from app.domains.ejemplo.service import crear_ejemplo

router = APIRouter()


@router.post("/", response_model=EjemploResponse, status_code=201)
async def create_ejemplo(data: EjemploCreate):
    return crear_ejemplo(data)


@router.get("/debug/db")
async def debug_db():
    """Endpoint temporal para diagnosticar conexión a MySQL."""
    s = get_settings()
    return {
        "host": s.mysql_host,
        "port": s.mysql_port,
        "user": s.mysql_user,
        "password_length": len(s.mysql_password),
        "password_preview": s.mysql_password[:5] + "***" + s.mysql_password[-3:] if len(s.mysql_password) > 8 else "TOO_SHORT",
        "database": s.mysql_database,
    }
