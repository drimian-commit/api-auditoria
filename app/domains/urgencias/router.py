import logging

from fastapi import APIRouter, HTTPException

from app.domains.urgencias.schemas import AuditoriaUrgenciasRequest, AuditoriaUrgenciasResponse
from app.domains.urgencias.service import auditar_urgencia

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/auditar", response_model=AuditoriaUrgenciasResponse, status_code=200)
async def auditar_atencion_urgencias(data: AuditoriaUrgenciasRequest):
    """
    Audita un registro individual de atención de urgencias.

    Solo requiere los IDs de la cuenta (gestion/internacion).
    El sistema obtiene automáticamente todos los datos clínicos de la BD
    y los evalúa contra guías internacionales (WHO, AHA, NICE, ERC, ACS, ACEP).
    """
    try:
        return auditar_urgencia(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Error en auditoría LLM: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado en auditoría: {e}")
        raise HTTPException(status_code=500, detail="Error interno al procesar la auditoría")
