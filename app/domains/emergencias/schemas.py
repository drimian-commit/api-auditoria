from pydantic import BaseModel, Field
from typing import List


# --- Request: solo los IDs de la cuenta ---

class AuditoriaEmergenciasRequest(BaseModel):
    cuenta_gestion: int = Field(description="Año de gestión de la cuenta (ej: 2025)")
    cuenta_internacion: int = Field(description="Número de internación (ej: 140954)")
    cuenta_id: int = Field(default=1, description="ID de la cuenta (por defecto: 1)")


# --- Response: resultado de la auditoría de emergencias ---
# Mismo modelo que urgencias (AuditoriaClinicaResultado)

class AuditoriaEmergenciasResponse(BaseModel):
    # Identificadores del caso
    id_medico: int = Field(description="ID del médico auditado")
    nombre_medico: str = Field(description="Nombre completo del médico")
    id_persona_paciente: int = Field(description="ID del paciente atendido")
    nombre_paciente: str = Field(description="Nombre completo del paciente")
    id_evolucion: int = Field(description="ID de la evolución clínica")
    fecha_atencion: str = Field(description="Fecha y hora de la atención")
    cuenta_gestion: int = Field(description="Año de gestión de la cuenta")
    cuenta_internacion: int = Field(description="Número de internación")
    diagnostico_urgencia: str = Field(description="Diagnóstico registrado")

    # Resultado de la evaluación
    cumple_guias: str = Field(description="'Sí' o 'No' - Cumplimiento de guías internacionales")
    score_calidad: int = Field(ge=0, le=100, description="Puntuación 0-100 de adherencia a guías")

    # Guías y criterios
    guias_aplicables: List[str] = Field(description="Guías internacionales aplicables")
    criterios_cumplidos: List[str] = Field(description="Criterios de guías que SÍ cumple")
    criterios_no_cumplidos: List[str] = Field(description="Criterios de guías que NO cumple")

    # Evaluación clínica detallada
    tratamiento_adecuado: str = Field(description="Evaluación del tratamiento según guías")
    tiempo_atencion: str = Field(description="Evaluación de la oportunidad de la atención")
    estudios_solicitados: str = Field(description="Evaluación de estudios complementarios")
    medicacion_apropiada: str = Field(description="Evaluación de la medicación prescrita")

    # Hallazgos y recomendaciones
    hallazgos_criticos: List[str] = Field(description="Hallazgos importantes o alertas")
    recomendaciones: List[str] = Field(description="Sugerencias de mejora basadas en guías")
    comentarios_adicionales: str = Field(description="Contexto adicional relevante")
