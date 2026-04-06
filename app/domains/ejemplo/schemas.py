from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EjemploCreate(BaseModel):
    nombre: str
    descripcion: str


class EjemploResponse(BaseModel):
    id: UUID
    nombre: str
    descripcion: str
    creado_en: datetime
