import logging

from fastapi import APIRouter, HTTPException

from app.core.schemas import AuditoriaRequest
from app.domains.cirugias.schemas import AuditoriaCirugiasResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/auditar",
    response_model=AuditoriaCirugiasResponse,
    status_code=200,
    summary="Auditar cirugía",
    description=(
        "Audita un registro individual de **cirugía** (Sector -1) "
        "contra el protocolo OMS de Cirugía Segura.\n\n"
        "**Flujo interno:**\n"
        "1. Consulta MySQL para obtener info del paciente, cirujano y fecha\n"
        "2. Obtiene historial quirúrgico completo: evaluación pre-quirúrgica "
        "(enfermería y médica), checklist OMS (Sign In, Time Out, Sign Out), "
        "informe anestésico con medicación, informe quirúrgico con tiempos, "
        "conteo de instrumental, equipo quirúrgico, signos vitales y laboratorios\n"
        "3. Envía al LLM (Claude) para evaluación de seguridad quirúrgica\n"
        "4. Retorna score de seguridad (0-100), estado de cada fase del checklist OMS, "
        "hallazgos críticos/menores, aspectos positivos y recomendaciones\n\n"
        "**Protocolo evaluado:** WHO Surgical Safety Checklist\n"
        "- **Sign In:** 8 puntos verificados antes de anestesia\n"
        "- **Time Out:** 5 puntos verificados antes de incisión\n"
        "- **Sign Out:** 6 puntos verificados antes de salir del quirófano\n\n"
        "**Score de seguridad:**\n"
        "- 90-100: Excelente\n"
        "- 70-89: Bueno\n"
        "- 50-69: Regular\n"
        "- <50: Deficiente\n\n"
        "**Tiempo estimado de respuesta:** 30-90 segundos (depende del LLM)."
    ),
    responses={
        200: {"description": "Auditoría completada exitosamente"},
        404: {"description": "Cuenta no encontrada, sin documentos quirúrgicos (tipos 7-13) o sin checklist OMS"},
        502: {"description": "Error en el servicio de IA (todos los reintentos fallaron)"},
        500: {"description": "Error interno del servidor"},
    },
)
async def auditar_cirugia_endpoint(data: AuditoriaRequest):
    from app.domains.cirugias.service import auditar_cirugia

    try:
        return auditar_cirugia(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Error en auditoría LLM: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado en auditoría de cirugía: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {type(e).__name__}: {e}")
