from datetime import datetime, timezone
from uuid import uuid4

from app.domains.ejemplo.schemas import EjemploCreate, EjemploResponse


def crear_ejemplo(data: EjemploCreate) -> EjemploResponse:
    return EjemploResponse(
        id=uuid4(),
        nombre=data.nombre,
        descripcion=data.descripcion,
        creado_en=datetime.now(timezone.utc),
    )
