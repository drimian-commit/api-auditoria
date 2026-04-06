import logging

from fastapi import APIRouter, HTTPException

from app.domains.cirugias.schemas import AuditoriaCirugiasRequest, AuditoriaCirugiasResponse
from app.domains.cirugias.service import auditar_cirugia

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/auditar", response_model=AuditoriaCirugiasResponse, status_code=200)
async def auditar_cirugia_endpoint(data: AuditoriaCirugiasRequest):
    """
    Audita un registro individual de cirugía.

    Solo requiere los IDs de la cuenta (gestion/internacion).
    El sistema obtiene automáticamente todos los datos quirúrgicos de la BD
    y los evalúa contra el protocolo OMS de cirugía segura
    (Sign In / Time Out / Sign Out).
    """
    try:
        return auditar_cirugia(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Error en auditoría LLM: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado en auditoría de cirugía: {e}")
        raise HTTPException(status_code=500, detail="Error interno al procesar la auditoría")
