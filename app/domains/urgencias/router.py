import logging

from fastapi import APIRouter, HTTPException

from app.domains.urgencias.schemas import AuditoriaUrgenciasRequest, AuditoriaUrgenciasResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/auditar",
    response_model=AuditoriaUrgenciasResponse,
    status_code=200,
    summary="Auditar atención de urgencias",
    description=(
        "Audita un registro individual de atención de **urgencias** (Sector 50) "
        "contra guías clínicas internacionales.\n\n"
        "**Flujo interno:**\n"
        "1. Consulta MySQL para obtener info del paciente, médico y fecha\n"
        "2. Obtiene historial clínico completo (evoluciones, signos vitales, "
        "medicamentos, laboratorios, imágenes, solicitudes)\n"
        "3. Envía al LLM (Claude) para evaluación del acto médico\n"
        "4. Retorna score de calidad (0-100), criterios cumplidos/no cumplidos, "
        "hallazgos críticos y recomendaciones\n\n"
        "**Guías evaluadas:** WHO, AHA, NICE, ERC, ACS, ACEP\n\n"
        "**Contexto:** Casos de menor complejidad que emergencias, "
        "tiempos de respuesta ligeramente más flexibles.\n\n"
        "**Tiempo estimado de respuesta:** 30-60 segundos (depende del LLM)."
    ),
    responses={
        200: {"description": "Auditoría completada exitosamente"},
        404: {"description": "Cuenta no encontrada o sin evoluciones clínicas"},
        502: {"description": "Error en el servicio de IA (todos los reintentos fallaron)"},
        500: {"description": "Error interno del servidor"},
    },
)
async def auditar_atencion_urgencias(data: AuditoriaUrgenciasRequest):
    from app.domains.urgencias.service import auditar_urgencia

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
