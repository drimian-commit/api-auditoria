import json
import logging
import time
from typing import Dict

import litellm

from app.config import get_settings
from app.domains.cirugias.repository import obtener_detalle_cirugia, obtener_informacion_cirugia
from app.core.schemas import AuditoriaRequest
from app.domains.cirugias.schemas import AuditoriaCirugiasResponse

logger = logging.getLogger(__name__)

PROMPT_SISTEMA = """
Eres un experto auditor médico especializado en SEGURIDAD QUIRÚRGICA.
Tu tarea es evaluar si el ACTO MÉDICO QUIRÚRGICO cumple con estándares internacionales.

═══════════════════════════════════════════════════════════════════════════════
⚠️ REGLA FUNDAMENTAL: EVALÚA EL ACTO MÉDICO, NO LA DOCUMENTACIÓN
═══════════════════════════════════════════════════════════════════════════════

✅ SÍ EVALÚA (Acto médico quirúrgico):
- ¿Se CONFIRMÓ la identidad del paciente antes de la inducción anestésica?
- ¿Se VERIFICÓ el sitio quirúrgico correcto?
- ¿Se ADMINISTRÓ profilaxis antibiótica en tiempo adecuado (≤60 min antes)?
- ¿Se REALIZÓ el conteo de instrumental y gasas?
- ¿Se VERIFICARON alergias antes de administrar medicamentos?
- ¿La técnica quirúrgica fue APROPIADA para el diagnóstico?
- ¿Se MANEJARON correctamente las complicaciones (si las hubo)?
- ¿El paciente salió ESTABLE del quirófano (Aldrete ≥8)?

❌ NO EVALÚES (Documentación):
- Si el formulario está "completo" o tiene todos los campos
- Si se "registró" o "documentó" algo
- Calidad de redacción o formato de notas
- Si "falta documentar" algo

REGLA DE ORO:
- Si una acción aparece en el historial → ASUME que SE REALIZÓ
- Si NO aparece → ASUME que NO SE REALIZÓ
- Evalúa si lo que se HIZO fue correcto, no si se escribió bien

═══════════════════════════════════════════════════════════════════════════════
PROTOCOLO OMS DE CIRUGÍA SEGURA (WHO Surgical Safety Checklist)
═══════════════════════════════════════════════════════════════════════════════

🔵 SIGN IN (Antes de inducción anestésica):
   □ Identidad del paciente confirmada
   □ Sitio quirúrgico marcado (si aplica)
   □ Procedimiento confirmado
   □ Consentimiento firmado
   □ Pulsioxímetro funcionando
   □ Alergias conocidas verificadas
   □ Vía aérea difícil evaluada
   □ Riesgo de hemorragia >500ml evaluado

🟡 TIME OUT (Antes de incisión cutánea):
   □ Todos los miembros del equipo se presentaron
   □ Confirmación de: paciente, sitio, procedimiento
   □ Profilaxis antibiótica administrada (últimos 60 min)
   □ Eventos críticos anticipados
   □ Imágenes esenciales mostradas

🟢 SIGN OUT (Antes de salir del quirófano):
   □ Nombre del procedimiento confirmado
   □ Conteo de instrumental completo
   □ Conteo de gasas/compresas completo
   □ Muestras etiquetadas correctamente
   □ Problemas de equipos documentados
   □ Plan de recuperación comunicado

═══════════════════════════════════════════════════════════════════════════════
CLASIFICACIÓN ASA (American Society of Anesthesiologists)
═══════════════════════════════════════════════════════════════════════════════
ASA I   = Paciente sano
ASA II  = Enfermedad sistémica leve (DM controlada, HTA leve, obesidad)
ASA III = Enfermedad sistémica grave (DM descompensada, ICC, EPOC)
ASA IV  = Enfermedad sistémica grave con amenaza vital
ASA V   = Paciente moribundo
ASA VI  = Muerte cerebral (donante de órganos)
""".strip()


def _construir_prompt_usuario(
    historial: str,
    cuenta_gestion: int,
    cuenta_internacion: int,
    id_paciente: int,
    nombre_paciente: str,
    fecha_cirugia: str,
    cirujano_principal: str,
) -> str:
    return f"""
Analiza la siguiente cirugía y evalúa el ACTO MÉDICO QUIRÚRGICO.

═══════════════════════════════════════════════════════════════════════════════
INFORMACIÓN DE LA CIRUGÍA
═══════════════════════════════════════════════════════════════════════════════
- Cuenta: {cuenta_gestion}/{cuenta_internacion}
- Paciente: {nombre_paciente} (ID: {id_paciente})
- Fecha de cirugía: {fecha_cirugia}
- Cirujano principal: {cirujano_principal}

═══════════════════════════════════════════════════════════════════════════════
HISTORIAL QUIRÚRGICO COMPLETO
═══════════════════════════════════════════════════════════════════════════════
{historial}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE EVALUACIÓN
═══════════════════════════════════════════════════════════════════════════════

1. EVALÚA cada fase del checklist OMS:
   - Sign In: ¿Se verificaron los 8 puntos ANTES de anestesia?
   - Time Out: ¿Se confirmaron los 5 puntos ANTES de cortar?
   - Sign Out: ¿Se verificaron los 6 puntos ANTES de salir?

2. EVALÚA la seguridad del acto quirúrgico:
   - ¿La indicación quirúrgica era correcta?
   - ¿La técnica fue apropiada?
   - ¿Se manejaron bien las complicaciones?
   - ¿El paciente salió estable?

3. IDENTIFICA:
   - Hallazgos CRÍTICOS (riesgo para el paciente)
   - Hallazgos menores (oportunidades de mejora)
   - Aspectos POSITIVOS (buenas prácticas)

4. ASIGNA un score de seguridad (0-100):
   - 90-100: Excelente, cumple todos los estándares
   - 70-89: Bueno, cumple mayoría con observaciones menores
   - 50-69: Regular, hay omisiones importantes
   - <50: Deficiente, hay riesgos significativos

═══════════════════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA (JSON)
═══════════════════════════════════════════════════════════════════════════════

Responde ÚNICAMENTE con un objeto JSON válido con estos campos:
- cumple_protocolo_oms: string ("Sí", "No", "Parcial")
- score_seguridad_quirurgica: integer (0-100)
- sign_in_completo: string ("Sí", "No", "Parcial", "No encontrado")
- sign_in_hallazgos: string (resumen de hallazgos)
- time_out_completo: string ("Sí", "No", "Parcial", "No encontrado")
- time_out_hallazgos: string (resumen de hallazgos)
- sign_out_completo: string ("Sí", "No", "Parcial", "No encontrado")
- sign_out_hallazgos: string (resumen de hallazgos)
- evaluacion_prequirurgica: string
- clasificacion_asa: string o null
- tecnica_anestesica: string o null
- procedimiento_realizado: string
- tiempos_quirurgicos: string
- manejo_complicaciones: string
- hallazgos_criticos: array de strings
- hallazgos_menores: array de strings
- aspectos_positivos: array de strings
- recomendaciones: array de strings
- comentarios_adicionales: string
- anestesiologo: string o null

NO incluyas: cuenta_gestion, cuenta_internacion, id_paciente, nombre_paciente,
fecha_cirugia, cirujano_principal, id_cirujano (los agregaré automáticamente).

Responde SOLO con el JSON, sin texto adicional ni bloques de código.
""".strip()


def formatear_cirugia_para_llm(detalle: Dict) -> str:
    """Formatea los datos de la cirugía en texto estructurado para el LLM."""

    texto = """
═══════════════════════════════════════════════════════════════════════════════
                        HISTORIAL QUIRÚRGICO COMPLETO
                    (Datos Estructurados del Checklist OMS)
═══════════════════════════════════════════════════════════════════════════════

"""

    # TIPO 7: EVALUACIÓN PRE-QUIRÚRGICA DE ENFERMERÍA
    if detalle.get("eval_prequirurgica_enfermeria"):
        texto += "─── EVALUACIÓN PRE-QUIRÚRGICA DE ENFERMERÍA ────────────────────────────────\n\n"
        try:
            data = json.loads(detalle["eval_prequirurgica_enfermeria"])
            texto += f"Fecha: {data.get('fecha', 'N/A')}\n"
            texto += f"Profesional: {data.get('profesional', 'N/A')}\n\n"
            texto += "PREPARACIÓN DEL PACIENTE:\n"
            texto += f"  - Ayuno: {data.get('ayuno', 'No registrado')}\n"
            texto += f"  - Enema evacuante: {data.get('enema_evacuante', 'No registrado')}\n"
            texto += f"  - Diuresis: {data.get('diuresis', 'No registrado')}\n"
            texto += f"  - Baño pre-quirúrgico: {data.get('bano_prequirurgico', 'No registrado')}\n"
            texto += f"  - Uñas limpias sin esmalte: {data.get('unas_limpias_sin_esmalte', 'No registrado')}\n"
            texto += f"  - Corte de vello en sitio quirúrgico: {data.get('corte_vello_sitio_quirurgico', 'No registrado')}\n"
            texto += f"  - Prótesis dental: {data.get('protesis_dental', 'No registrado')}\n"
            texto += f"  - Lentes de contacto/anteojos: {data.get('lentes_contacto_anteojos', 'No registrado')}\n"
            texto += f"  - Objetos de valor: {data.get('objetos_de_valor', 'No registrado')}\n"
            texto += f"  - ¿Con anestesia/sedación?: {data.get('con_anestesia_sedacion', 'No registrado')}\n\n"
        except Exception:
            texto += f"{detalle['eval_prequirurgica_enfermeria']}\n\n"

    # TIPO 8: EVALUACIÓN PRE-QUIRÚRGICA MÉDICA
    if detalle.get("eval_prequirurgica_medica"):
        texto += "─── EVALUACIÓN PRE-QUIRÚRGICA MÉDICA ─────────────────────────────────────────\n\n"
        try:
            data = json.loads(detalle["eval_prequirurgica_medica"])
            texto += f"Fecha: {data.get('fecha', 'N/A')}\n"
            texto += f"Médico evaluador: {data.get('profesional', 'N/A')}\n\n"
            texto += f"Enfermedad actual: {data.get('enfermedad_actual', 'No registrado')}\n"
            texto += f"Tipo de cirugía: {data.get('tipo_cirugia', 'No registrado')}\n"
            texto += f"Tipo de programación: {data.get('tipo_programacion', 'No registrado')}\n"
        except Exception:
            texto += f"{detalle['eval_prequirurgica_medica']}\n"

        if detalle.get("diagnostico_preoperatorio"):
            texto += f"\nDiagnóstico preoperatorio: {detalle['diagnostico_preoperatorio']}\n"
        if detalle.get("procedimiento_previsto"):
            texto += f"Procedimiento previsto: {detalle['procedimiento_previsto']}\n"
        texto += "\n"

    # TIPO 10: SIGN IN
    texto += "─── SIGN IN - Lista de Verificación (ANTES DE ANESTESIA) ─────────────────────\n\n"

    if detalle.get("sign_in_info"):
        try:
            data = json.loads(detalle["sign_in_info"])
            texto += f"Fecha/Hora: {data.get('fecha', 'N/A')}\n"
            texto += f"Responsable: {data.get('profesional', 'N/A')}\n\n"
        except Exception:
            pass

    if detalle.get("sign_in_checklist"):
        texto += "CHECKLIST OMS - SIGN IN:\n"
        for line in detalle["sign_in_checklist"].split("\n"):
            if line.strip():
                texto += f"  {line}\n"
        texto += "\n"
    else:
        texto += "⚠️ CHECKLIST SIGN IN: No encontrado o vacío\n\n"

    if detalle.get("equipo_quirurgico_sign_in"):
        texto += "EQUIPO QUIRÚRGICO CONFIRMADO:\n"
        for line in detalle["equipo_quirurgico_sign_in"].split("\n"):
            if line.strip():
                texto += f"  - {line}\n"
        texto += "\n"

    # TIPO 11: TIME OUT
    texto += "─── TIME OUT - Lista de Verificación (ANTES DE INCISIÓN) ─────────────────────\n\n"

    if detalle.get("time_out_info"):
        try:
            data = json.loads(detalle["time_out_info"])
            texto += f"Fecha/Hora: {data.get('fecha', 'N/A')}\n"
            texto += f"Responsable: {data.get('profesional', 'N/A')}\n\n"
        except Exception:
            pass

    if detalle.get("time_out_checklist"):
        texto += "CHECKLIST OMS - TIME OUT:\n"
        for line in detalle["time_out_checklist"].split("\n"):
            if line.strip():
                texto += f"  {line}\n"
        texto += "\n"
    else:
        texto += "⚠️ CHECKLIST TIME OUT: No encontrado o vacío\n\n"

    if detalle.get("equipo_quirurgico_time_out"):
        texto += "EQUIPO QUIRÚRGICO CONFIRMADO:\n"
        for line in detalle["equipo_quirurgico_time_out"].split("\n"):
            if line.strip():
                texto += f"  - {line}\n"
        texto += "\n"

    # TIPO 9: INFORME ANESTÉSICO
    if detalle.get("informe_anestesico"):
        texto += "─── INFORME ANESTÉSICO ─────────────────────────────────────────────────────\n\n"
        try:
            data = json.loads(detalle["informe_anestesico"])
            texto += f"Fecha: {data.get('fecha', 'N/A')}\n"
            texto += f"Anestesiólogo: {data.get('anestesiologo', 'N/A')}\n\n"
            texto += f"Clasificación ASA: {data.get('score_asa', 'No registrado')}\n"
            texto += f"Tipo de anestesia: {data.get('tipo_anestesia', 'No especificado')}\n"
            texto += f"Nivel anestésico: {data.get('nivel_anestesia', 'No especificado')}\n"
            texto += f"Intubación: {data.get('intubacion', 'No')}\n"
            texto += f"Máscara: {data.get('mascara', 'No')}\n\n"
            texto += "TIEMPOS DE ANESTESIA:\n"
            texto += f"  - Inicio: {data.get('fecha_hora_inicio_anestesia', 'No registrado')}\n"
            texto += f"  - Fin: {data.get('fecha_hora_fin_anestesia', 'No registrado')}\n\n"
            texto += f"Estado final del paciente: {data.get('estado_final_paciente', 'No registrado')}\n"
            texto += f"Observaciones: {data.get('observaciones', 'Sin observaciones')}\n\n"
        except Exception:
            texto += f"{detalle['informe_anestesico']}\n\n"

    if detalle.get("medicacion_anestesica"):
        texto += "MEDICACIÓN ANESTÉSICA ADMINISTRADA:\n"
        for line in detalle["medicacion_anestesica"].split("\n"):
            if line.strip():
                texto += f"  - {line}\n"
        texto += "\n"

    # TIPO 13: INFORME QUIRÚRGICO
    if detalle.get("informe_quirurgico"):
        texto += "─── INFORME QUIRÚRGICO ─────────────────────────────────────────────────────\n\n"
        try:
            data = json.loads(detalle["informe_quirurgico"])
            texto += f"Fecha: {data.get('fecha', 'N/A')}\n"
            texto += f"Cirujano principal: {data.get('cirujano', 'N/A')}\n\n"
            texto += "TIEMPOS QUIRÚRGICOS:\n"
            texto += f"  - Inicio de cirugía: {data.get('fecha_hora_inicio_cirugia', 'No registrado')}\n"
            texto += f"  - Fin de cirugía: {data.get('fecha_hora_fin_cirugia', 'No registrado')}\n\n"

            if data.get("descripcion_procedimiento"):
                texto += f"DESCRIPCIÓN DEL PROCEDIMIENTO:\n{data.get('descripcion_procedimiento')}\n\n"
        except Exception:
            texto += f"{detalle['informe_quirurgico']}\n\n"

        if detalle.get("diagnostico_postoperatorio"):
            texto += f"Diagnóstico postoperatorio: {detalle['diagnostico_postoperatorio']}\n"
        if detalle.get("operacion_practicada"):
            texto += f"Operación practicada: {detalle['operacion_practicada']}\n"
        texto += "\n"

    if detalle.get("equipo_quirurgico_informe"):
        texto += "EQUIPO QUIRÚRGICO:\n"
        for line in detalle["equipo_quirurgico_informe"].split("\n"):
            if line.strip():
                texto += f"  - {line}\n"
        texto += "\n"

    # TIPO 12: SIGN OUT
    texto += "─── SIGN OUT - Lista de Verificación (ANTES DE SALIR DEL QUIRÓFANO) ──────────\n\n"

    if detalle.get("sign_out_info"):
        try:
            data = json.loads(detalle["sign_out_info"])
            texto += f"Fecha/Hora: {data.get('fecha', 'N/A')}\n"
            texto += f"Responsable: {data.get('profesional', 'N/A')}\n\n"
        except Exception:
            pass

    if detalle.get("sign_out_checklist"):
        texto += "CHECKLIST OMS - SIGN OUT:\n"
        for line in detalle["sign_out_checklist"].split("\n"):
            if line.strip():
                texto += f"  {line}\n"
        texto += "\n"
    else:
        texto += "⚠️ CHECKLIST SIGN OUT: No encontrado o vacío\n\n"

    # CONTEO DE INSTRUMENTAL
    if detalle.get("conteo_instrumental"):
        texto += "*** CONTEO DE INSTRUMENTAL ***\n"
        try:
            conteo = json.loads(detalle["conteo_instrumental"])
            texto += f"  - Gasas: {conteo.get('gasas', 'N/A')}\n"
            texto += f"  - Agujas: {conteo.get('agujas', 'N/A')}\n"
            texto += f"  - Apósitos: {conteo.get('apositos', 'N/A')}\n"
            texto += f"  - Compresas: {conteo.get('compresas', 'N/A')}\n"
        except Exception:
            texto += f"  {detalle['conteo_instrumental']}\n"
        texto += "\n"

    # SIGNOS VITALES
    if detalle.get("signos_vitales"):
        texto += "─── SIGNOS VITALES ─────────────────────────────────────────────────────────\n\n"
        texto += f"{detalle['signos_vitales']}\n\n"

    # MEDICAMENTOS ADMINISTRADOS
    if detalle.get("ejecuciones_medicamentos"):
        texto += "─── MEDICAMENTOS ADMINISTRADOS ─────────────────────────────────────────────\n\n"
        texto += f"{detalle['ejecuciones_medicamentos']}\n\n"

    # LABORATORIOS
    if detalle.get("laboratorios"):
        texto += "─── LABORATORIOS ───────────────────────────────────────────────────────────\n\n"
        texto += f"{detalle['laboratorios']}\n\n"

    texto += "═" * 80 + "\n"
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


def auditar_cirugia(data: AuditoriaRequest) -> AuditoriaCirugiasResponse:
    """Ejecuta la auditoría completa de un registro individual de cirugía."""

    gestion = data.cuenta_gestion
    internacion = data.cuenta_internacion
    cuenta_id = 1

    # 1. Obtener información básica de la BD
    info = obtener_informacion_cirugia(gestion, internacion)
    if not info:
        raise ValueError(
            f"No se encontró cirugía en la cuenta {gestion}/{internacion}. "
            "Verifique que la cuenta exista y tenga documentos quirúrgicos (tipos 7-13)."
        )

    id_paciente = info["id_paciente"]
    nombre_paciente = info["nombre_paciente"]
    cirujano = info["cirujano"] or "No identificado"
    id_cirujano = info["id_cirujano"] or 0
    fecha_cirugia = str(info["fecha_cirugia"])
    cuenta_id = info.get("cuenta_id", cuenta_id)

    # 2. Obtener detalle clínico completo
    detalle = obtener_detalle_cirugia(id_paciente, gestion, internacion, cuenta_id)
    if not detalle:
        raise ValueError(
            f"La cuenta {gestion}/{internacion} no tiene datos quirúrgicos estructurados."
        )

    # Validar que tengamos al menos algún dato quirúrgico
    campos_criticos = ["informe_quirurgico", "sign_in_checklist", "time_out_checklist"]
    if not any(detalle.get(campo) for campo in campos_criticos):
        raise ValueError(
            f"La cuenta {gestion}/{internacion} no tiene checklist OMS ni informe quirúrgico."
        )

    # 3. Formatear historial para el LLM
    historial = formatear_cirugia_para_llm(detalle)

    # 4. Construir prompt y llamar al LLM
    prompt_usuario = _construir_prompt_usuario(
        historial=historial,
        cuenta_gestion=gestion,
        cuenta_internacion=internacion,
        id_paciente=id_paciente,
        nombre_paciente=nombre_paciente,
        fecha_cirugia=fecha_cirugia,
        cirujano_principal=cirujano,
    )

    resultado_llm = _llamar_llm(prompt_usuario)

    # 5. Agregar campos conocidos
    resultado_llm["cuenta_gestion"] = gestion
    resultado_llm["cuenta_internacion"] = internacion
    resultado_llm["id_paciente"] = id_paciente
    resultado_llm["nombre_paciente"] = nombre_paciente
    resultado_llm["fecha_cirugia"] = fecha_cirugia
    resultado_llm["cirujano_principal"] = cirujano
    resultado_llm["id_cirujano"] = id_cirujano

    # 6. Validar y retornar
    return AuditoriaCirugiasResponse(**resultado_llm)
