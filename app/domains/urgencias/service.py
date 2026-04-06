import json
import logging
import time
from typing import Dict

import litellm

from app.config import get_settings
from app.domains.urgencias.repository import obtener_detalle_atencion, obtener_informacion_basica
from app.core.schemas import AuditoriaRequest
from app.domains.urgencias.schemas import AuditoriaUrgenciasResponse

logger = logging.getLogger(__name__)

PROMPT_SISTEMA = """
Eres un experto auditor médico especializado en medicina de urgencias.
Tu tarea es evaluar si la atención de urgencias proporcionada cumple con guías clínicas
internacionales reconocidas como:
- WHO (World Health Organization)
- AHA (American Heart Association)
- NICE (National Institute for Health and Care Excellence)
- ERC (European Resuscitation Council)
- ACS (American College of Surgeons)
- ACEP (American College of Emergency Physicians)

⚠️ CONTEXTO DE URGENCIAS:
- Este servicio atiende casos de menor complejidad que emergencias críticas
- Los tiempos de respuesta pueden ser ligeramente más flexibles que en emergencias
- Sin embargo, se deben seguir las mismas guías internacionales
- Evaluar según estándares de calidad apropiados para urgencias

⚠️ IMPORTANTE - SOLO EVALÚA EL ACTO MÉDICO, NO LA DOCUMENTACIÓN:

✅ SÍ EVALÚA (Acto médico clínico):
- ¿Se administró el tratamiento correcto según guías? (dosis, vía, medicamento)
- ¿Se solicitaron los estudios clínicos necesarios? (laboratorios, imágenes)
- ¿El diagnóstico fue correcto y oportuno según la presentación?
- ¿Los tiempos de atención cumplieron con lo recomendado?
- ¿Se realizaron los procedimientos clínicos necesarios?
- ¿Se dio el seguimiento clínico apropiado?
- ¿Se prescribieron medicamentos ambulatorios necesarios?

❌ NO EVALÚES (Documentación):
- Si algo está "documentado" o "registrado" en notas
- Si se "escribió" o no algo en el expediente
- Completitud de formularios o registros
- Calidad del llenado de documentación

REGLA DE ORO:
- Si una acción clínica aparece en el historial (ej: "se administró adrenalina"), ASUME que se realizó
- Si NO aparece en el historial, ASUME que NO se realizó
- Evalúa si lo que se HIZO fue correcto según guías, no si se documentó bien

⚠️ IMPORTANTE - INTERPRETACIÓN DE LABORATORIOS:
El historial tiene DOS secciones de laboratorios:
1. "RESULTADOS DE LABORATORIO": Laboratorios con resultados ya disponibles
2. "SOLICITUDES DE LABORATORIO (ÓRDENES MÉDICAS)": TODOS los laboratorios solicitados (con o sin resultado)

REGLAS DE INTERPRETACIÓN:
- Si un laboratorio aparece en "SOLICITUDES DE LABORATORIO", el médico SÍ LO SOLICITÓ
- Un laboratorio puede estar SOLICITADO pero sin resultado aún (ej: urocultivo tarda 48-72h)
- NO digas "no se solicitó X" si X aparece en la sección de SOLICITUDES
- La sección de SOLICITUDES es la fuente de verdad sobre qué ordenó el médico
- La sección de RESULTADOS solo muestra los que ya tienen valores

Ejemplo correcto:
- Si ves "Estudio: UROCULTIVO | Fecha solicitud: 2025-12-01" en SOLICITUDES → SÍ se solicitó
- Aunque no aparezca en RESULTADOS (porque tarda días), el médico SÍ cumplió con solicitarlo

Solo evalúa como "no solicitado" si el estudio NO aparece en NINGUNA de las dos secciones.

⚠️ IMPORTANTE - INTERPRETACIÓN DE ESTUDIOS DE IMAGEN:
El historial tiene DOS secciones de imágenes:
1. "ESTUDIOS DE IMAGEN": Imágenes con informe radiológico ya disponible
2. "SOLICITUDES DE IMAGEN (ÓRDENES MÉDICAS)": TODOS los estudios solicitados (con o sin informe)

REGLAS DE INTERPRETACIÓN:
- Si un estudio aparece en "SOLICITUDES DE IMAGEN", el médico SÍ LO SOLICITÓ
- Un estudio puede estar SOLICITADO pero sin informe aún (ej: RX pendiente de lectura)
- NO digas "no se solicitó RX/TAC/ECO" si aparece en la sección de SOLICITUDES
- La sección de SOLICITUDES DE IMAGEN es la fuente de verdad sobre qué ordenó el médico
- La sección de ESTUDIOS DE IMAGEN solo muestra los que ya tienen informe radiológico

Ejemplo correcto:
- Si ves "Estudio: Radiografía Torax Posteroanterior | Fecha solicitud: 2025-12-03" en SOLICITUDES → SÍ se solicitó
- Aunque no aparezca en ESTUDIOS DE IMAGEN (porque no tiene informe), el médico SÍ cumplió con solicitarlo

Solo evalúa como "no solicitado" si el estudio NO aparece en NINGUNA de las dos secciones de imagen.

⚠️ IMPORTANTE - INTERPRETACIÓN DE TIEMPOS DE OBSERVACIÓN E INTERNACIÓN:
- Si el paciente fue INTERNADO (pasó a piso/hospitalización), la observación CONTINÚA en internación
- NO penalices "tiempo insuficiente en urgencias" si hubo decisión de internación
- Ejemplo: Guías recomiendan 6 horas de observación → 2h en urgencias + internación = CUMPLE (observación continúa)
- La internación es una decisión CORRECTA para observación prolongada
- Solo evalúa el tiempo en urgencias si el paciente fue dado de ALTA a domicilio directamente
- Frases clave que indican internación: "INDICA INTERNACIÓN", "PASA A PISO", "TRASLADO A PISO", "INGRESA A PISO"
""".strip()


def _construir_prompt_usuario(
    historial: str,
    id_evolucion: int,
    fecha_atencion: str,
    diagnostico: str,
    id_persona: int,
    id_medico: int,
    nombre_medico: str,
) -> str:
    return f"""
Analiza la siguiente atención de urgencias y auditala según guías médicas internacionales.

**Información de la atención:**
- ID Evolución: {id_evolucion}
- Fecha de atención: {fecha_atencion}
- Diagnóstico registrado: {diagnostico}
- ID Paciente: {id_persona}
- ID Médico: {id_medico}
- Médico tratante: {nombre_medico}

**Historial Clínico del Paciente:**
{historial}

**Instrucciones de Evaluación:**

1. Identifica las guías internacionales que aplican al caso

2. Evalúa el ACTO MÉDICO CLÍNICO:
   - Diagnóstico: ¿Fue oportuno y certero?
   - Estudios: ¿Los labs/imágenes solicitados fueron apropiados?
   - Tratamiento: ¿Medicamentos/procedimientos administrados correctos según guías?
   - Tiempos: ¿Cumplieron tiempos recomendados? (considerando contexto de urgencias)
   - Seguimiento: ¿El tiempo de observación fue adecuado?
   - Prescripción ambulatoria: ¿Se dieron los medicamentos/dispositivos necesarios al alta?

3. Ejemplos de lo que SÍ debes evaluar:
   ✅ "Administró adrenalina 0.5mg cuando la dosis correcta es 0.3mg"
   ✅ "No prescribió EpiPen al alta en un caso de anafilaxia"
   ✅ "Dio de alta a DOMICILIO a la 1 hora cuando se requieren 4-6 horas" (SOLO si NO fue internado)
   ✅ "No solicitó triptasa sérica en anafilaxia" (SOLO si NO aparece en solicitudes)
   ✅ "No refirió a alergología pese a ser la cuarta reacción"

4. Ejemplos de lo que NO debes evaluar:
   ❌ "No documentó la búsqueda de angioedema"
   ❌ "Falta documentar criterios de anafilaxia"
   ❌ "No se registró educación al paciente"
   ❌ "Completitud de registros insuficiente"
   ❌ "Tiempo de observación insuficiente en urgencias" → Si muestra "INDICA INTERNACIÓN"

5. Asigna un score de calidad del acto médico (0-100)
6. Identifica fortalezas y áreas de mejora EN LA PRÁCTICA CLÍNICA
7. Recomendaciones para mejorar EL ACTO MÉDICO, no la documentación

**IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido con esta estructura:**
- cumple_guias: string ("Sí" o "No")
- score_calidad: integer (0-100)
- guias_aplicables: array de strings
- criterios_cumplidos: array de strings
- criterios_no_cumplidos: array de strings
- tratamiento_adecuado: string
- tiempo_atencion: string
- estudios_solicitados: string
- medicacion_apropiada: string
- hallazgos_criticos: array de strings
- recomendaciones: array de strings
- comentarios_adicionales: string

NO incluyas los campos id_medico, nombre_medico, id_persona_paciente, id_evolucion, fecha_atencion, diagnostico_urgencia, nombre_paciente, cuenta_gestion, cuenta_internacion.
Responde SOLO con el JSON, sin texto adicional.
""".strip()


def formatear_historial(detalle: Dict) -> str:
    """Formatea los datos clínicos del detalle de BD en texto estructurado para el LLM."""

    evoluciones = []
    if detalle.get("evoluciones_clinicas"):
        evo_raw = detalle["evoluciones_clinicas"]
        if "---EVOLUCION---" in evo_raw:
            evo_parts = evo_raw.split("\n---EVOLUCION---\n")
        else:
            evo_parts = [evo_raw]

        for evo_json in evo_parts:
            try:
                evoluciones.append(json.loads(evo_json))
            except json.JSONDecodeError:
                pass

    texto = f"""
=================================================================================
ATENCIÓN DE URGENCIAS - DETALLE COMPLETO
=================================================================================

INFORMACIÓN DE LA CUENTA:
- Paciente ID: {detalle.get('persona_numero')}
- Gestión: {detalle.get('cuenta_gestion')}
- Número de Internación: {detalle.get('cuenta_internacion')}
- ID de Cuenta: {detalle.get('cuenta_id')}

=================================================================================
EVOLUCIONES CLÍNICAS
=================================================================================
"""

    for i, evo in enumerate(evoluciones, 1):
        texto += f"\n--- Evolución #{i} ---\n"
        texto += f"Fecha: {evo.get('fecha', 'N/A')}\n"
        texto += f"Tipo: {evo.get('tipo_evento', 'N/A')}\n"
        texto += f"Profesional: {evo.get('profesional', 'N/A')}\n"

        if evo.get("diagnosticos"):
            texto += f"\nDiagnósticos CIE9:\n{evo['diagnosticos']}\n"
        if evo.get("comentario_clinico"):
            texto += f"\nComentario Clínico:\n{evo['comentario_clinico']}\n"
        if evo.get("plan_medico"):
            texto += f"\nPlan Médico:\n{evo['plan_medico']}\n"
        if evo.get("medicamentos_prescritos"):
            texto += f"\nMedicamentos Prescritos:\n{evo['medicamentos_prescritos']}\n"

        texto += "-" * 80 + "\n"

    if detalle.get("signos_vitales"):
        texto += f"""
=================================================================================
SIGNOS VITALES
=================================================================================
{detalle['signos_vitales']}

"""

    if detalle.get("ejecuciones_medicamentos"):
        texto += f"""
=================================================================================
EJECUCIONES DE MEDICAMENTOS (ENFERMERÍA)
=================================================================================
{detalle['ejecuciones_medicamentos']}

"""

    if detalle.get("notas_enfermeria"):
        texto += f"""
=================================================================================
NOTAS DE ENFERMERÍA
=================================================================================
{detalle['notas_enfermeria']}

"""

    if detalle.get("laboratorios"):
        texto += f"""
=================================================================================
RESULTADOS DE LABORATORIO
=================================================================================
{detalle['laboratorios']}

"""

    if detalle.get("estudios_imagen"):
        imagenes = detalle["estudios_imagen"].split("\n---IMAGEN---\n")
        texto += """
=================================================================================
ESTUDIOS DE IMAGEN
=================================================================================
"""
        for img in imagenes:
            texto += f"{img}\n{'-' * 80}\n"

    if detalle.get("solicitudes_laboratorio"):
        texto += f"""
=================================================================================
SOLICITUDES DE LABORATORIO (ÓRDENES MÉDICAS)
=================================================================================
NOTA: Esta sección muestra TODOS los laboratorios SOLICITADOS por el médico,
independientemente de si ya tienen resultado. Un estudio que aparece aquí
FUE SOLICITADO aunque no tenga resultado en la sección anterior.

{detalle['solicitudes_laboratorio']}


"""

    if detalle.get("solicitudes_imagen"):
        texto += f"""
=================================================================================
SOLICITUDES DE IMAGEN (ÓRDENES MÉDICAS)
=================================================================================
NOTA: Esta sección muestra TODOS los estudios de imagen SOLICITADOS por el médico
(RX, TAC, Ecografías, RM, etc.), independientemente de si ya tienen informe.
Un estudio que aparece aquí FUE SOLICITADO aunque no tenga resultado/informe
en la sección "ESTUDIOS DE IMAGEN" anterior.

{detalle['solicitudes_imagen']}

"""

    texto += "=" * 80 + "\n"
    return texto


def _llamar_llm(prompt_usuario: str) -> dict:
    """Llama al LLM con reintentos y fallback de modelo."""
    settings = get_settings()

    modelos = [
        f"openrouter/{settings.default_model}",
        f"openrouter/{settings.fallback_model}",
    ]

    litellm.drop_params = True
    litellm.set_verbose = False

    reintentos = 3

    for modelo in modelos:
        for intento in range(reintentos):
            try:
                response = litellm.completion(
                    model=modelo,
                    messages=[
                        {"role": "system", "content": PROMPT_SISTEMA},
                        {"role": "user", "content": prompt_usuario},
                    ],
                    temperature=0.3,
                )

                content = response.choices[0].message.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                return json.loads(content)

            except Exception as e:
                logger.warning(f"Intento {intento + 1}/{reintentos} fallido con {modelo}: {e}")
                time.sleep(2**intento)

        logger.warning(f"Fallaron todos los intentos con {modelo}, probando siguiente modelo...")

    raise RuntimeError("Fallaron todos los modelos e intentos de auditoría LLM")


def auditar_urgencia(data: AuditoriaRequest) -> AuditoriaUrgenciasResponse:
    """Ejecuta la auditoría completa de un registro individual de urgencias."""

    gestion = data.cuenta_gestion
    internacion = data.cuenta_internacion

    # 1. Obtener información básica de la BD
    info = obtener_informacion_basica(gestion, internacion)
    if not info:
        raise ValueError(
            f"No se encontró la cuenta {gestion}/{internacion}. "
            "Verifique que la gestión y número de internación sean correctos."
        )

    persona_numero = info["id_persona_paciente"]
    cuenta_id = info.get("cuenta_id", 1)
    nombre_paciente = info["nombre_paciente"]
    nombre_medico = info["nombre_medico"]
    id_medico = info["id_medico"]
    fecha_atencion = str(info["fecha_atencion"])

    # 2. Obtener detalle clínico completo
    detalle = obtener_detalle_atencion(persona_numero, gestion, internacion, cuenta_id)
    if not detalle or not detalle.get("evoluciones_clinicas"):
        raise ValueError(
            f"La cuenta {gestion}/{internacion} no tiene evoluciones clínicas registradas."
        )

    # 3. Formatear historial para el LLM
    historial = formatear_historial(detalle)

    diagnostico = "Diagnóstico de urgencia - Ver evoluciones clínicas"

    # 4. Construir prompt y llamar al LLM
    prompt_usuario = _construir_prompt_usuario(
        historial=historial,
        id_evolucion=0,
        fecha_atencion=fecha_atencion,
        diagnostico=diagnostico,
        id_persona=persona_numero,
        id_medico=id_medico,
        nombre_medico=nombre_medico,
    )

    resultado_llm = _llamar_llm(prompt_usuario)

    # 5. Agregar campos conocidos
    resultado_llm["id_medico"] = id_medico
    resultado_llm["nombre_medico"] = nombre_medico
    resultado_llm["id_persona_paciente"] = persona_numero
    resultado_llm["nombre_paciente"] = nombre_paciente
    resultado_llm["id_evolucion"] = 0
    resultado_llm["fecha_atencion"] = fecha_atencion
    resultado_llm["cuenta_gestion"] = gestion
    resultado_llm["cuenta_internacion"] = internacion
    resultado_llm["diagnostico_urgencia"] = diagnostico

    # 6. Validar y retornar
    return AuditoriaUrgenciasResponse(**resultado_llm)
