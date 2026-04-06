import logging

from fastapi import APIRouter, HTTPException

from app.domains.emergencias.schemas import AuditoriaEmergenciasRequest, AuditoriaEmergenciasResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/auditar",
    response_model=AuditoriaEmergenciasResponse,
    status_code=200,
    summary="Auditar atención de emergencias",
    description=(
        "Audita un registro individual de atención de **emergencias** (Sector 3) "
        "contra guías clínicas internacionales.\n\n"
        "**Flujo interno:**\n"
        "1. Consulta MySQL para obtener info del paciente, médico y fecha\n"
        "2. Obtiene historial clínico completo (evoluciones, signos vitales, "
        "medicamentos, laboratorios, imágenes, solicitudes)\n"
        "3. Envía al LLM (Claude) para evaluación del acto médico\n"
        "4. Retorna score de calidad (0-100), criterios cumplidos/no cumplidos, "
        "hallazgos críticos y recomendaciones\n\n"
        "**Guías evaluadas:** WHO, AHA, NICE, ERC, ACS, ACEP\n\n"
        "**Contexto:** Casos de **alta complejidad y criticidad**. "
        "Tiempos de respuesta estrictos según protocolos de reanimación, "
        "trauma, IAM, ACV, etc.\n\n"
        "**Tiempo estimado de respuesta:** 30-60 segundos (depende del LLM)."
    ),
    responses={
        200: {"description": "Auditoría completada exitosamente"},
        404: {"description": "Cuenta no encontrada en emergencias (sector 3) o sin evoluciones"},
        502: {"description": "Error en el servicio de IA (todos los reintentos fallaron)"},
        500: {"description": "Error interno del servidor"},
    },
)
async def auditar_atencion_emergencias(data: AuditoriaEmergenciasRequest):
    from app.domains.emergencias.service import auditar_emergencia

    try:
        return auditar_emergencia(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Error en auditoría LLM: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado en auditoría: {e}")
        raise HTTPException(status_code=500, detail="Error interno al procesar la auditoría")
