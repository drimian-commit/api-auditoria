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

app = FastAPI(title="API Auditoria", version="0.1.0")

register_exception_handlers(app)

app.include_router(ejemplo_router, prefix="/api/v1/ejemplo", tags=["Ejemplo"])
app.include_router(urgencias_router, prefix="/api/v1/urgencias", tags=["Urgencias"])
app.include_router(cirugias_router, prefix="/api/v1/cirugias", tags=["Cirugías"])
app.include_router(emergencias_router, prefix="/api/v1/emergencias", tags=["Emergencias"])
