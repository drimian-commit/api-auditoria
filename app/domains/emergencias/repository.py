import logging
import os
from typing import Any, Dict, List, Optional

import pymysql
from pymysql.cursors import DictCursor

from app.config import get_settings

logger = logging.getLogger(__name__)

_QUERIES_DIR = os.path.join(os.path.dirname(__file__), "queries")


def _load_query(name: str) -> str:
    path = os.path.join(_QUERIES_DIR, f"{name}.sql")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _get_connection() -> pymysql.Connection:
    settings = get_settings()
    conn = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        cursorclass=DictCursor,
        connect_timeout=10,
    )
    with conn.cursor() as cursor:
        cursor.execute("SET SESSION group_concat_max_len = 10485760")
    return conn


def _execute_query(query: str) -> Optional[List[Dict[str, Any]]]:
    conn = _get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall() or []
    finally:
        conn.close()


def obtener_informacion_basica(
    gestion: int, internacion: int
) -> Optional[Dict[str, Any]]:
    """Obtiene info básica de la atención de emergencia: paciente, médico, fecha.

    Diferencia con urgencias:
    - Sector 3 (emergencias), no sector 50 (urgencias)
    - Sin filtro por TurnoTipo
    """
    query = f"""
    SELECT
        pe.PersonaNumero AS id_persona_paciente,
        MIN(pe.PacienteEvolucionFechaHora) AS fecha_atencion,
        (SELECT u2.UsuarioPersonaCodigo
         FROM pacienteevolucion pe2
         LEFT JOIN usuario u2 ON u2.UsuarioCodigo = pe2.PacienteEvolucionMUsuario
         WHERE pe2.PacienteEvolucionGestion = pe.PacienteEvolucionGestion
           AND pe2.PacienteEvolucionNroInter = pe.PacienteEvolucionNroInter
         ORDER BY pe2.PacienteEvolucionFechaHora ASC
         LIMIT 1) AS id_medico,
        (SELECT med2.PersonaNombreCompleto
         FROM pacienteevolucion pe2
         LEFT JOIN usuario u2 ON u2.UsuarioCodigo = pe2.PacienteEvolucionMUsuario
         LEFT JOIN persona med2 ON med2.PersonaNumero = u2.UsuarioPersonaCodigo
         WHERE pe2.PacienteEvolucionGestion = pe.PacienteEvolucionGestion
           AND pe2.PacienteEvolucionNroInter = pe.PacienteEvolucionNroInter
         ORDER BY pe2.PacienteEvolucionFechaHora ASC
         LIMIT 1) AS nombre_medico,
        pac.PersonaNombreCompleto AS nombre_paciente
    FROM pacienteevolucion pe
    LEFT JOIN persona pac ON pac.PersonaNumero = pe.PersonaNumero
    WHERE pe.PacienteEvolucionGestion = {gestion}
      AND pe.PacienteEvolucionNroInter = {internacion}
      AND pe.PacienteEvolucionSector = 3
      AND pe.PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    GROUP BY
        pe.PersonaNumero,
        pac.PersonaNombreCompleto,
        pe.PacienteEvolucionGestion,
        pe.PacienteEvolucionNroInter
    LIMIT 1
    """
    results = _execute_query(query)
    if results and len(results) > 0:
        return results[0]
    return None


def obtener_detalle_atencion(
    persona_numero: int, cuenta_gestion: int, cuenta_internacion: int, cuenta_id: int
) -> Optional[Dict[str, Any]]:
    """Obtiene el detalle clínico completo de una atención de emergencia."""
    query_template = _load_query("get_detalle_atencion")
    query = query_template.format(
        persona_numero=persona_numero,
        cuenta_gestion=cuenta_gestion,
        cuenta_internacion=cuenta_internacion,
        cuenta_id=cuenta_id,
    )
    results = _execute_query(query)
    if results and len(results) > 0:
        return results[0]
    return None
