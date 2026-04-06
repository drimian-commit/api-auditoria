from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


class AuditoriaRequest(BaseModel):
    """Request compartido para todos los endpoints de auditoría.

    Solo requiere gestión y número de internación para identificar el caso.
    """
    cuenta_gestion: int = Field(
        description="Año de gestión de la cuenta",
        json_schema_extra={"examples": [2026]},
    )
    cuenta_internacion: int = Field(
        description="Número de internación",
        json_schema_extra={"examples": [45588]},
    )
