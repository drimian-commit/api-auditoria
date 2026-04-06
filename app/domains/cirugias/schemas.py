from pydantic import BaseModel, Field
from typing import List, Optional


# --- Request: solo los IDs de la cuenta ---

class AuditoriaCirugiasRequest(BaseModel):
    cuenta_gestion: int = Field(description="Año de gestión de la cuenta (ej: 2025)")
    cuenta_internacion: int = Field(description="Número de internación (ej: 12223)")
    cuenta_id: int = Field(default=1, description="ID de la cuenta (por defecto: 1)")


# --- Response: resultado de la auditoría quirúrgica ---

class AuditoriaCirugiasResponse(BaseModel):
    # Identificadores
    cuenta_gestion: int = Field(description="Año de gestión de la cuenta")
    cuenta_internacion: int = Field(description="Número de internación")
    id_paciente: int = Field(description="ID del paciente")
    nombre_paciente: str = Field(description="Nombre completo del paciente")
    fecha_cirugia: str = Field(description="Fecha y hora de la cirugía")

    # Equipo quirúrgico
    cirujano_principal: str = Field(description="Nombre del cirujano principal")
    id_cirujano: int = Field(description="ID del cirujano principal")
    anestesiologo: Optional[str] = Field(default=None, description="Nombre del anestesiólogo")

    # Evaluación general
    cumple_protocolo_oms: str = Field(description="Sí/No/Parcial - Cumplimiento protocolo OMS")
    score_seguridad_quirurgica: int = Field(ge=0, le=100, description="Puntuación 0-100 de seguridad quirúrgica")

    # Checklists OMS
    sign_in_completo: str = Field(description="Sí/No/Parcial/No encontrado")
    sign_in_hallazgos: str = Field(description="Hallazgos específicos del Sign In")
    time_out_completo: str = Field(description="Sí/No/Parcial/No encontrado")
    time_out_hallazgos: str = Field(description="Hallazgos específicos del Time Out")
    sign_out_completo: str = Field(description="Sí/No/Parcial/No encontrado")
    sign_out_hallazgos: str = Field(description="Hallazgos específicos del Sign Out")

    # Evaluaciones específicas
    evaluacion_prequirurgica: str = Field(description="Evaluación de la preparación pre-quirúrgica")
    clasificacion_asa: Optional[str] = Field(default=None, description="Clasificación ASA (I-V)")
    tecnica_anestesica: Optional[str] = Field(default=None, description="Técnica anestésica utilizada")
    procedimiento_realizado: str = Field(description="Descripción del procedimiento quirúrgico")
    tiempos_quirurgicos: str = Field(description="Evaluación de tiempos quirúrgicos")
    manejo_complicaciones: str = Field(description="Evaluación del manejo de complicaciones")

    # Hallazgos y recomendaciones
    hallazgos_criticos: List[str] = Field(description="Problemas graves de seguridad identificados")
    hallazgos_menores: List[str] = Field(description="Observaciones menores")
    aspectos_positivos: List[str] = Field(description="Buenas prácticas identificadas")
    recomendaciones: List[str] = Field(description="Sugerencias de mejora")
    comentarios_adicionales: str = Field(description="Contexto adicional relevante")
