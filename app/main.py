import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.domains.ejemplo.router import router as ejemplo_router
from app.domains.urgencias.router import router as urgencias_router
from app.domains.cirugias.router import router as cirugias_router
from app.domains.emergencias.router import router as emergencias_router

load_dotenv()

settings = get_settings()
os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key

app = FastAPI(
    title="API Auditoria Medica",
    version="0.1.0",
    description=(
        "API para auditoría automatizada del acto médico en Clínica Foianini.\n\n"
        "Evalúa registros individuales de atención contra guías clínicas internacionales "
        "(WHO, AHA, NICE, ERC, ACS, ACEP, OMS Cirugía Segura) utilizando IA (Claude via OpenRouter).\n\n"
        "## Dominios\n\n"
        "| Dominio | Sector BD | Descripción |\n"
        "|---------|-----------|-------------|\n"
        "| **Urgencias** | Sector 50 | Casos de menor complejidad, tiempos flexibles |\n"
        "| **Emergencias** | Sector 3 | Casos de alta complejidad, tiempos estrictos |\n"
        "| **Cirugías** | Sector -1 | Checklist OMS: Sign In / Time Out / Sign Out |\n\n"
        "## Uso\n\n"
        "Todos los endpoints de auditoría reciben solo `cuenta_gestion` + `cuenta_internacion`. "
        "El sistema consulta la BD automáticamente para obtener el historial clínico completo."
    ),
    contact={"name": "Sistema de Auditoría CAF", "email": "no.responder@correo-caf.com"},
)

register_exception_handlers(app)

app.include_router(ejemplo_router, prefix="/api/v1/ejemplo", tags=["Ejemplo"])
app.include_router(urgencias_router, prefix="/api/v1/urgencias", tags=["Urgencias"])
app.include_router(cirugias_router, prefix="/api/v1/cirugias", tags=["Cirugías"])
app.include_router(emergencias_router, prefix="/api/v1/emergencias", tags=["Emergencias"])
