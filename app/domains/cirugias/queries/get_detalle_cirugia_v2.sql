-- ═══════════════════════════════════════════════════════════════════════════════
-- GET_DETALLE_CIRUGIA_V2.SQL
-- Versión mejorada con datos estructurados del checklist OMS
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- PARÁMETROS (usar .format() en Python):
--   {persona_numero}     - ID del paciente
--   {cuenta_gestion}     - Año de gestión (ej: 2025)
--   {cuenta_internacion} - Número de internación
--   {cuenta_id}          - ID de cuenta
--
-- VERSIÓN: 2.0.0
-- FECHA: 2025-12-04
-- CAMBIOS:
--   - Integra datos estructurados de checklist OMS
--   - Incluye equipo quirúrgico completo
--   - Incluye conteo de instrumental (Sign Out)
--   - Incluye medicación anestésica con dosis
--   - Incluye tiempos exactos de cirugía y anestesia
-- ═══════════════════════════════════════════════════════════════════════════════

SELECT
    -- Información básica
    '{persona_numero}' AS persona_numero,
    '{cuenta_gestion}' AS cuenta_gestion,
    '{cuenta_internacion}' AS cuenta_internacion,
    '{cuenta_id}' AS cuenta_id,

    -- ═══════════════════════════════════════════════════════════════════════════
    -- TIPO 7: EVALUACIÓN PRE-QUIRÚRGICA DE ENFERMERÍA
    -- ═══════════════════════════════════════════════════════════════════════════
    (
        SELECT JSON_OBJECT(
            'fecha', premed.PacienteEvolucionFechaHora,
            'profesional', medico.PersonaNombreCompleto,
            'ayuno', CASE
                WHEN PacienteEvolucionAyuno = 1 THEN CONCAT('SI - Hora inicio: ', COALESCE(PacienteEvolucionAyunaHora, 'No especificada'))
                WHEN PacienteEvolucionAyuno = 2 THEN 'NO'
                WHEN PacienteEvolucionAyuno = 3 THEN 'NO APLICA'
                ELSE 'No registrado'
            END,
            'enema_evacuante', CASE
                WHEN PacienteEvolucionEnemaEva = 1 THEN CONCAT('SI - Hora: ', COALESCE(PacienteEvolucionEnemaEvaHora, 'No especificada'))
                WHEN PacienteEvolucionEnemaEva = 2 THEN 'NO'
                WHEN PacienteEvolucionEnemaEva = 3 THEN 'NO APLICA'
                ELSE 'No registrado'
            END,
            'diuresis', CASE
                WHEN PacienteEvolucionDiuresis = 1 THEN 'ESPONTANEA'
                WHEN PacienteEvolucionDiuresis = 2 THEN 'SONDA VESICAL'
                ELSE 'No registrado'
            END,
            'bano_prequirurgico', CASE
                WHEN PacienteEvolucionBanoPre = 1 THEN 'SI'
                WHEN PacienteEvolucionBanoPre = 2 THEN 'NO'
                WHEN PacienteEvolucionBanoPre = 3 THEN 'NO APLICA'
                ELSE 'No registrado'
            END,
            'unas_limpias_sin_esmalte', CASE
                WHEN PacienteEvolucionUnaSinES = 1 THEN 'SI'
                WHEN PacienteEvolucionUnaSinES = 2 THEN 'NO'
                WHEN PacienteEvolucionUnaSinES = 3 THEN 'NO APLICA'
                ELSE 'No registrado'
            END,
            'corte_vello_sitio_quirurgico', CASE
                WHEN PacienteEvolucionCorteVello = 1 THEN 'SI'
                WHEN PacienteEvolucionCorteVello = 2 THEN 'NO'
                WHEN PacienteEvolucionCorteVello = 3 THEN 'NO APLICA'
                ELSE 'No registrado'
            END,
            'protesis_dental', CASE
                WHEN PacienteEvolucionProtesisDen = 1 THEN 'SI'
                WHEN PacienteEvolucionProtesisDen = 2 THEN 'NO'
                WHEN PacienteEvolucionProtesisDen = 3 THEN 'NO APLICA'
                ELSE 'No registrado'
            END,
            'lentes_contacto_anteojos', CASE
                WHEN PacienteEvolucionLentesContact = 1 THEN 'SI'
                WHEN PacienteEvolucionLentesContact = 2 THEN 'NO'
                WHEN PacienteEvolucionLentesContact = 3 THEN 'NO APLICA'
                ELSE 'No registrado'
            END,
            'objetos_de_valor', CASE
                WHEN PacienteEvolucionObjetoValor = 1 THEN CONCAT('ENTREGADO A FAMILIAR: ', COALESCE(PacienteEvolucionObjetoValNom, 'No especificado'))
                WHEN PacienteEvolucionObjetoValor = 2 THEN CONCAT('ENTREGADO A AMIGO: ', COALESCE(PacienteEvolucionObjetoValNom, 'No especificado'))
                WHEN PacienteEvolucionObjetoValor = 3 THEN CONCAT('ENTREGADO A ADMINISTRACION: ', COALESCE(PacienteEvolucionObjetoValNom, 'No especificado'))
                WHEN PacienteEvolucionObjetoValor = 4 THEN 'NO APLICA'
                ELSE 'No registrado'
            END,
            'con_anestesia_sedacion', CASE
                WHEN PacienteEvolucionEsConAnestesi = 1 THEN 'SI'
                ELSE 'NO'
            END
        )
        FROM pacienteevolucion premed
        INNER JOIN usuario ON UsuarioCodigo = PacienteEvolucionMUsuario
        INNER JOIN persona medico ON medico.PersonaNumero = UsuarioPersonaCodigo
        WHERE PacienteEvolucionTipo = 7
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
        LIMIT 1
    ) AS eval_prequirurgica_enfermeria,

    -- ═══════════════════════════════════════════════════════════════════════════
    -- TIPO 8: EVALUACIÓN PRE-QUIRÚRGICA MÉDICA
    -- ═══════════════════════════════════════════════════════════════════════════
    (
        SELECT JSON_OBJECT(
            'fecha', premed.PacienteEvolucionFechaHora,
            'profesional', medico.PersonaNombreCompleto,
            'enfermedad_actual', PacienteEvolucionSubjetivo,
            'tipo_cirugia', CASE
                WHEN PacienteEvolucionTipoCirugia = '1' THEN 'Hospitalizado'
                ELSE 'Ambulatoria'
            END,
            'tipo_programacion', CASE
                WHEN PacienteEvolucionTipoProgramac = '2' THEN 'Programado'
                ELSE 'Emergencia'
            END
        )
        FROM pacienteevolucion premed
        INNER JOIN usuario ON UsuarioCodigo = PacienteEvolucionMUsuario
        INNER JOIN persona medico ON medico.PersonaNumero = UsuarioPersonaCodigo
        WHERE PacienteEvolucionTipo = 8
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
        LIMIT 1
    ) AS eval_prequirurgica_medica,

    -- Diagnóstico preoperatorio (para tipo 8)
    (
        SELECT GROUP_CONCAT(
            CONCAT('[', cie9cm.CIE9CMCodigo, '] ', cie9cm.CIE9CMDescripcion)
            SEPARATOR ' | '
        )
        FROM pacienteevolucion premed
        INNER JOIN pacienteevoluciondiagnostico diag ON
            diag.PersonaNumero = premed.PersonaNumero AND
            diag.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN cie9cm ON cie9cm.CIE9CMCodigo = diag.CIE9CMCodigo
        WHERE PacienteEvolucionTipo = 8
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS diagnostico_preoperatorio,

    -- Procedimiento previsto (para tipo 8)
    (
        SELECT GROUP_CONCAT(
            CONCAT('[CIE9-CM:', proced.CodProcedimiento, '] ', proced.Descripcion)
            SEPARATOR ' | '
        )
        FROM pacienteevolucion premed
        INNER JOIN pacienteevoluciontratamiento proc ON
            proc.PersonaNumero = premed.PersonaNumero AND
            proc.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN clinica01.procedimientos proced ON proced.CodProcedimiento = proc.PacienteEvolucionTratamientoCo
        WHERE PacienteEvolucionTipo = 8
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS procedimiento_previsto,

    -- ═══════════════════════════════════════════════════════════════════════════
    -- TIPO 10: SIGN IN - Lista de Verificación (Antes de Anestesia)
    -- ═══════════════════════════════════════════════════════════════════════════
    (
        SELECT JSON_OBJECT(
            'fecha', premed.PacienteEvolucionFechaHora,
            'profesional', medico.PersonaNombreCompleto
        )
        FROM pacienteevolucion premed
        INNER JOIN usuario ON UsuarioCodigo = PacienteEvolucionMUsuario
        INNER JOIN persona medico ON medico.PersonaNumero = UsuarioPersonaCodigo
        WHERE PacienteEvolucionTipo = 10
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
        LIMIT 1
    ) AS sign_in_info,

    (
        SELECT GROUP_CONCAT(
            CONCAT(
                'PREGUNTA: ', pregpreguntadescripcion,
                ' | RESPUESTA: ', RespuestaNombre,
                CASE WHEN VerificacionPreguntasDescripci IS NOT NULL AND VerificacionPreguntasDescripci != ''
                     THEN CONCAT(' | COMENTARIO: ', VerificacionPreguntasDescripci)
                     ELSE ''
                END
            )
            SEPARATOR '\n'
        )
        FROM pacienteevolucion premed
        INNER JOIN verificacion verifi ON
            verifi.PersonaNumero = premed.PersonaNumero AND
            verifi.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN verificacionpreguntas pregunta ON
            pregunta.PersonaNumero = verifi.PersonaNumero AND
            pregunta.PacienteEvolucionFechaHora = verifi.PacienteEvolucionFechaHora AND
            pregunta.VerificacionCodigo = verifi.VerificacionCodigo
        INNER JOIN preguntas ON
            preguntas.pregpreguntanumero = pregunta.pregpreguntanumero AND
            preguntas.pregpreguntanumero <> 22
        INNER JOIN respuesta ON respuesta.RespuestaCodigo = pregunta.VerificacionPreguntasEscogida
        INNER JOIN usuario ON UsuarioCodigo = PacienteEvolucionMUsuario
        INNER JOIN persona medico ON medico.PersonaNumero = UsuarioPersonaCodigo
        WHERE PacienteEvolucionTipo = 10
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS sign_in_checklist,

    -- Equipo quirúrgico del Sign In
    (
        SELECT GROUP_CONCAT(
            DISTINCT CONCAT(partiPersona.PersonaNombreCompleto, ' - ', funcion.Descripcion)
            SEPARATOR '\n'
        )
        FROM pacienteevolucion premed
        INNER JOIN verificacionparticipante verifiparti ON
            verifiparti.PersonaNumero = premed.PersonaNumero AND
            verifiparti.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN persona partiPersona ON partiPersona.PersonaNumero = ParticipanteNumero
        INNER JOIN clinica01.internamedicosfunc funcion ON funcion.CodEqMedFuncion = MedicosFuncionCodigo
        WHERE PacienteEvolucionTipo = 10
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS equipo_quirurgico_sign_in,

    -- ═══════════════════════════════════════════════════════════════════════════
    -- TIPO 11: TIME OUT - Lista de Verificación (Antes de Incisión)
    -- ═══════════════════════════════════════════════════════════════════════════
    (
        SELECT JSON_OBJECT(
            'fecha', premed.PacienteEvolucionFechaHora,
            'profesional', medico.PersonaNombreCompleto
        )
        FROM pacienteevolucion premed
        INNER JOIN usuario ON UsuarioCodigo = PacienteEvolucionMUsuario
        INNER JOIN persona medico ON medico.PersonaNumero = UsuarioPersonaCodigo
        WHERE PacienteEvolucionTipo = 11
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
        LIMIT 1
    ) AS time_out_info,

    (
        SELECT GROUP_CONCAT(
            CONCAT(
                'PREGUNTA: ', pregpreguntadescripcion,
                ' | RESPUESTA: ', RespuestaNombre,
                CASE WHEN VerificacionPreguntasDescripci IS NOT NULL AND VerificacionPreguntasDescripci != ''
                     THEN CONCAT(' | COMENTARIO: ', VerificacionPreguntasDescripci)
                     ELSE ''
                END
            )
            SEPARATOR '\n'
        )
        FROM pacienteevolucion premed
        INNER JOIN verificacion verifi ON
            verifi.PersonaNumero = premed.PersonaNumero AND
            verifi.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN verificacionpreguntas pregunta ON
            pregunta.PersonaNumero = verifi.PersonaNumero AND
            pregunta.PacienteEvolucionFechaHora = verifi.PacienteEvolucionFechaHora AND
            pregunta.VerificacionCodigo = verifi.VerificacionCodigo
        INNER JOIN preguntas ON
            preguntas.pregpreguntanumero = pregunta.pregpreguntanumero AND
            preguntas.pregpreguntanumero <> 22
        INNER JOIN respuesta ON respuesta.RespuestaCodigo = pregunta.VerificacionPreguntasEscogida
        INNER JOIN usuario ON UsuarioCodigo = PacienteEvolucionMUsuario
        INNER JOIN persona medico ON medico.PersonaNumero = UsuarioPersonaCodigo
        WHERE PacienteEvolucionTipo = 11
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS time_out_checklist,

    -- Equipo quirúrgico del Time Out
    (
        SELECT GROUP_CONCAT(
            DISTINCT CONCAT(partiPersona.PersonaNombreCompleto, ' - ', funcion.Descripcion)
            SEPARATOR '\n'
        )
        FROM pacienteevolucion premed
        INNER JOIN verificacionparticipante verifiparti ON
            verifiparti.PersonaNumero = premed.PersonaNumero AND
            verifiparti.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN persona partiPersona ON partiPersona.PersonaNumero = ParticipanteNumero
        INNER JOIN clinica01.internamedicosfunc funcion ON funcion.CodEqMedFuncion = MedicosFuncionCodigo
        WHERE PacienteEvolucionTipo = 11
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS equipo_quirurgico_time_out,

    -- ═══════════════════════════════════════════════════════════════════════════
    -- TIPO 12: SIGN OUT - Lista de Verificación (Antes de Salir)
    -- ═══════════════════════════════════════════════════════════════════════════
    (
        SELECT JSON_OBJECT(
            'fecha', premed.PacienteEvolucionFechaHora,
            'profesional', medico.PersonaNombreCompleto
        )
        FROM pacienteevolucion premed
        INNER JOIN usuario ON UsuarioCodigo = PacienteEvolucionMUsuario
        INNER JOIN persona medico ON medico.PersonaNumero = UsuarioPersonaCodigo
        WHERE PacienteEvolucionTipo = 12
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
        LIMIT 1
    ) AS sign_out_info,

    (
        SELECT GROUP_CONCAT(
            CONCAT(
                'PREGUNTA: ', pregpreguntadescripcion,
                ' | RESPUESTA: ', RespuestaNombre,
                CASE WHEN VerificacionPreguntasDescripci IS NOT NULL AND VerificacionPreguntasDescripci != ''
                     THEN CONCAT(' | COMENTARIO: ', VerificacionPreguntasDescripci)
                     ELSE ''
                END
            )
            SEPARATOR '\n'
        )
        FROM pacienteevolucion premed
        INNER JOIN verificacion verifi ON
            verifi.PersonaNumero = premed.PersonaNumero AND
            verifi.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN verificacionpreguntas pregunta ON
            pregunta.PersonaNumero = verifi.PersonaNumero AND
            pregunta.PacienteEvolucionFechaHora = verifi.PacienteEvolucionFechaHora AND
            pregunta.VerificacionCodigo = verifi.VerificacionCodigo
        INNER JOIN preguntas ON
            preguntas.pregpreguntanumero = pregunta.pregpreguntanumero AND
            preguntas.pregpreguntanumero <> 22
        INNER JOIN respuesta ON respuesta.RespuestaCodigo = pregunta.VerificacionPreguntasEscogida
        INNER JOIN usuario ON UsuarioCodigo = PacienteEvolucionMUsuario
        INNER JOIN persona medico ON medico.PersonaNumero = UsuarioPersonaCodigo
        WHERE PacienteEvolucionTipo = 12
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS sign_out_checklist,

    -- CONTEO DE INSTRUMENTAL (Sign Out) - CRÍTICO PARA AUDITORÍA
    (
        SELECT JSON_OBJECT(
            'gasas', MAX(VerificacionPreguntasGasas),
            'agujas', MAX(VerificacionPreguntasAgujas),
            'apositos', MAX(VerificacionPreguntasAspositos),
            'compresas', MAX(VerificacionPreguntasCompresas)
        )
        FROM pacienteevolucion premed
        INNER JOIN verificacion verifi ON
            verifi.PersonaNumero = premed.PersonaNumero AND
            verifi.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN verificacionpreguntas pregunta ON
            pregunta.PersonaNumero = verifi.PersonaNumero AND
            pregunta.PacienteEvolucionFechaHora = verifi.PacienteEvolucionFechaHora AND
            pregunta.VerificacionCodigo = verifi.VerificacionCodigo
        WHERE PacienteEvolucionTipo = 12
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS conteo_instrumental,

    -- ═══════════════════════════════════════════════════════════════════════════
    -- TIPO 9: INFORME ANESTÉSICO
    -- ═══════════════════════════════════════════════════════════════════════════
    (
        SELECT JSON_OBJECT(
            'fecha', premed.PacienteEvolucionFechaHora,
            'anestesiologo', medico.PersonaNombreCompleto,
            'score_asa', CASE
                WHEN PacienteEvolucionAnesAsa = 1 THEN 'I'
                WHEN PacienteEvolucionAnesAsa = 2 THEN 'II'
                WHEN PacienteEvolucionAnesAsa = 3 THEN 'III'
                WHEN PacienteEvolucionAnesAsa = 4 THEN 'IV'
                WHEN PacienteEvolucionAnesAsa = 5 THEN 'V'
                WHEN PacienteEvolucionAnesAsa = 6 THEN 'VI'
                ELSE 'No registrado'
            END,
            'fecha_hora_inicio_anestesia', PacienteEvolucionAnesaFechaini,
            'fecha_hora_fin_anestesia', PacienteEvolucionAnesaFechaFin,
            'tipo_anestesia', COALESCE(tipoanestesia.AnesteciaPerinatalDescripcion, 'No especificado'),
            'nivel_anestesia', CASE
                WHEN PacienteEvolucionNivelAnestesi = 1 THEN 'T8-T9'
                WHEN PacienteEvolucionNivelAnestesi = 2 THEN 'T9-T10'
                WHEN PacienteEvolucionNivelAnestesi = 3 THEN 'T10-T11'
                WHEN PacienteEvolucionNivelAnestesi = 4 THEN 'T11-T12'
                WHEN PacienteEvolucionNivelAnestesi = 5 THEN 'T12-L1'
                WHEN PacienteEvolucionNivelAnestesi = 6 THEN 'L1-L2'
                WHEN PacienteEvolucionNivelAnestesi = 7 THEN 'L2-L3'
                WHEN PacienteEvolucionNivelAnestesi = 8 THEN 'L3-L4'
                WHEN PacienteEvolucionNivelAnestesi = 9 THEN 'L4-L5'
                ELSE 'No especificado'
            END,
            'intubacion', CASE
                WHEN PacienteEvolucionAnesIntubacio = 'TOT' THEN 'Tubo Orotraqueal'
                WHEN PacienteEvolucionAnesIntubacio = 'TNT' THEN 'Tubo Nasotraqueal'
                ELSE 'NO'
            END,
            'mascara', CASE
                WHEN PacienteEvolucionAnesMascara = 'F' THEN 'Facial'
                WHEN PacienteEvolucionAnesMascara = 'L' THEN 'Laringea'
                ELSE 'NO'
            END,
            'observaciones', COALESCE(NULLIF(PacienteEvolucionAnesObserva, ''), 'Sin observaciones'),
            'estado_final_paciente', COALESCE(PacienteEvolucionanesestadofin, 'No registrado')
        )
        FROM pacienteevolucion premed
        INNER JOIN usuario ON UsuarioCodigo = PacienteEvolucionMUsuario
        INNER JOIN persona medico ON medico.PersonaNumero = UsuarioPersonaCodigo
        LEFT JOIN tipoanestesia ON tipoanestesia.AnesteciaPerinatalCodigo = premed.AnesteciaPerinatalCodigo
        WHERE PacienteEvolucionTipo = 9
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
        LIMIT 1
    ) AS informe_anestesico,

    -- Medicación anestésica con dosis y vía
    (
        SELECT GROUP_CONCAT(
            DISTINCT CONCAT(
                atc.ATCNombre, ' ',
                CASE WHEN medicamento.PacienteMedicamentoDosis = FLOOR(medicamento.PacienteMedicamentoDosis)
                     THEN CAST(medicamento.PacienteMedicamentoDosis AS UNSIGNED)
                     ELSE medicamento.PacienteMedicamentoDosis
                END, ' ', unidad.UnidadDescripcion,
                ' vía ', via.Descripcion
            )
            SEPARATOR '\n'
        )
        FROM pacienteevolucion premed
        INNER JOIN pacienteevolucionmedicamento medicamento ON
            medicamento.PersonaNumero = premed.PersonaNumero AND
            medicamento.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN atc ON atc.ATCCodigo = medicamento.ATCCodigo
        INNER JOIN unidad ON unidad.UnidadCodigo = medicamento.UnidadCodigo
        INNER JOIN clinica01.vias via ON via.CodVia = medicamento.ViaEvoCodigo
        WHERE PacienteEvolucionTipo = 9
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS medicacion_anestesica,

    -- Equipo quirúrgico del informe anestésico
    (
        SELECT GROUP_CONCAT(
            DISTINCT CONCAT(partiPersona.PersonaNombreCompleto, ' - ', funcion.Descripcion)
            SEPARATOR '\n'
        )
        FROM pacienteevolucion premed
        INNER JOIN verificacionparticipante verifiparti ON
            verifiparti.PersonaNumero = premed.PersonaNumero AND
            verifiparti.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN persona partiPersona ON partiPersona.PersonaNumero = ParticipanteNumero
        INNER JOIN clinica01.internamedicosfunc funcion ON funcion.CodEqMedFuncion = MedicosFuncionCodigo
        WHERE PacienteEvolucionTipo = 9
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS equipo_quirurgico_anestesia,

    -- ═══════════════════════════════════════════════════════════════════════════
    -- TIPO 13: INFORME QUIRÚRGICO
    -- ═══════════════════════════════════════════════════════════════════════════
    (
        SELECT JSON_OBJECT(
            'fecha', premed.PacienteEvolucionFechaHora,
            'cirujano', medico.PersonaNombreCompleto,
            'descripcion_procedimiento', COALESCE(PacienteEvolucionDescripProcQu, 'No registrado'),
            'fecha_hora_inicio_cirugia', PacienteEvolucionInicioCirugia,
            'fecha_hora_fin_cirugia', PacienteEvolucionFinCirugia
        )
        FROM pacienteevolucion premed
        INNER JOIN usuario ON UsuarioCodigo = PacienteEvolucionMUsuario
        INNER JOIN persona medico ON medico.PersonaNumero = UsuarioPersonaCodigo
        WHERE PacienteEvolucionTipo = 13
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
        LIMIT 1
    ) AS informe_quirurgico,

    -- Diagnóstico postoperatorio
    (
        SELECT GROUP_CONCAT(
            DISTINCT CONCAT('[', postcie9cm.CIE9CMCodigo, '] ', postcie9cm.CIE9CMDescripcion)
            SEPARATOR ' | '
        )
        FROM pacienteevolucion premed
        INNER JOIN postdiagnostico ON
            postdiagnostico.PersonaNumero = premed.PersonaNumero AND
            postdiagnostico.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN cie9cm postcie9cm ON postcie9cm.CIE9CMCodigo = postdiagnostico.DiagnosticoPostOpeCodigo
        WHERE PacienteEvolucionTipo = 13
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS diagnostico_postoperatorio,

    -- Operación practicada
    (
        SELECT GROUP_CONCAT(
            DISTINCT CONCAT('[CIE9-CM:', proced.CodProcedimiento, '] ', proced.Descripcion)
            SEPARATOR ' | '
        )
        FROM pacienteevolucion premed
        INNER JOIN pacienteevoluciontratamiento proc ON
            proc.PersonaNumero = premed.PersonaNumero AND
            proc.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN clinica01.procedimientos proced ON proced.CodProcedimiento = proc.PacienteEvolucionTratamientoCo
        WHERE PacienteEvolucionTipo = 13
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS operacion_practicada,

    -- Equipo quirúrgico del informe quirúrgico
    (
        SELECT GROUP_CONCAT(
            DISTINCT CONCAT(partiPersona.PersonaNombreCompleto, ' - ', funcion.Descripcion)
            SEPARATOR '\n'
        )
        FROM pacienteevolucion premed
        INNER JOIN verificacionparticipante verifiparti ON
            verifiparti.PersonaNumero = premed.PersonaNumero AND
            verifiparti.PacienteEvolucionFechaHora = premed.PacienteEvolucionFechaHora
        INNER JOIN persona partiPersona ON partiPersona.PersonaNumero = ParticipanteNumero
        INNER JOIN clinica01.internamedicosfunc funcion ON funcion.CodEqMedFuncion = MedicosFuncionCodigo
        WHERE PacienteEvolucionTipo = 13
          AND premed.PersonaNumero = {persona_numero}
          AND PacienteEvolucionNroInter = {cuenta_internacion}
          AND PacienteEvolucionGestion = {cuenta_gestion}
          AND PacienteEvolucionNroIntId = {cuenta_id}
          AND PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS equipo_quirurgico_informe,

    -- ═══════════════════════════════════════════════════════════════════════════
    -- SIGNOS VITALES (del período quirúrgico)
    -- ═══════════════════════════════════════════════════════════════════════════
    (
        SELECT GROUP_CONCAT(
            CONCAT(fecha_registro, ': ', descripcion, ' = ', valor, ' ', COALESCE(unidad, ''))
            SEPARATOR ' | '
        )
        FROM vw_hc_signos_vitales
        WHERE persona_numero = {persona_numero}
          AND cuenta_gestion = {cuenta_gestion}
          AND cuenta_internacion = {cuenta_internacion}
          AND cuenta_id = {cuenta_id}
        ORDER BY fecha_registro ASC
    ) AS signos_vitales,

    -- ═══════════════════════════════════════════════════════════════════════════
    -- EJECUCIONES DE MEDICAMENTOS (desde clinica01)
    -- ═══════════════════════════════════════════════════════════════════════════
    (
        SELECT GROUP_CONCAT(
            CONCAT(
                'Fecha: ', mc.FechaReg,
                ' | Medicamento: ', COALESCE(ia.IvDescrip, 'No especificado'),
                ' | Cantidad: ', COALESCE(md.Cantidad, ''),
                ' | Enfermera: ', mc.Usuario
            )
            SEPARATOR '\n'
        )
        FROM clinica01.medicamentosc mc
        LEFT JOIN clinica01.medicamentosd md
            ON md.Gestion = mc.Gestion
            AND md.NroInternacion = mc.NroInternacion
            AND md.NroMedicamento = mc.NroMedicamento
        LEFT JOIN clinica01.ivarticulos ia ON ia.IvcodArticulo = md.IvCodArticulo
        WHERE mc.Gestion = {cuenta_gestion}
          AND mc.NroInternacion = {cuenta_internacion}
        ORDER BY mc.FechaReg ASC
    ) AS ejecuciones_medicamentos,

    -- ═══════════════════════════════════════════════════════════════════════════
    -- LABORATORIOS PREOPERATORIOS
    -- ═══════════════════════════════════════════════════════════════════════════
    (
        SELECT GROUP_CONCAT(
            DISTINCT CONCAT(
                'Servicio: ', descripcion_servicio,
                ' | Fecha: ', fecha_orden,
                ' | Resultados: ', linea_detalle, ': ', resultado, ' ', COALESCE(unidad, ''),
                ' (Ref: ', COALESCE(valor_referencia, 'N/A'), ')'
            )
            SEPARATOR '\n'
        )
        FROM vw_hc_resultados_laboratorio
        WHERE persona_numero = {persona_numero}
          AND cuenta_gestion = {cuenta_gestion}
          AND cuenta_internacion = {cuenta_internacion}
          AND cuenta_id = {cuenta_id}
        ORDER BY fecha_orden ASC
    ) AS laboratorios

FROM DUAL;
