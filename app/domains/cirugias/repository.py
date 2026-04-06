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
        charset="utf8mb4",
        ssl_disabled=True,
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


def obtener_informacion_cirugia(
    gestion: int, internacion: int
) -> Optional[Dict[str, Any]]:
    """Obtiene info básica de la cirugía: paciente, cirujano, fecha."""
    query = f"""
    SELECT
        pe.PersonaNumero AS id_paciente,
        pe.PacienteEvolucionNroIntId AS cuenta_id,
        pac.PersonaNombreCompleto AS nombre_paciente,
        MIN(pe.PacienteEvolucionFechaHora) AS fecha_cirugia,
        (SELECT med.PersonaNombreCompleto
         FROM pacienteevolucion pe2
         JOIN usuario u ON u.UsuarioCodigo = pe2.PacienteEvolucionMUsuario
         JOIN persona med ON med.PersonaNumero = u.UsuarioPersonaCodigo
         WHERE pe2.PacienteEvolucionTipo = 13
           AND pe2.PacienteEvolucionGestion = pe.PacienteEvolucionGestion
           AND pe2.PacienteEvolucionNroInter = pe.PacienteEvolucionNroInter
           AND pe2.PacienteEvolucionBFecha = '1000-01-01 00:00:00'
         LIMIT 1) AS cirujano,
        (SELECT u.UsuarioPersonaCodigo
         FROM pacienteevolucion pe2
         JOIN usuario u ON u.UsuarioCodigo = pe2.PacienteEvolucionMUsuario
         WHERE pe2.PacienteEvolucionTipo = 13
           AND pe2.PacienteEvolucionGestion = pe.PacienteEvolucionGestion
           AND pe2.PacienteEvolucionNroInter = pe.PacienteEvolucionNroInter
           AND pe2.PacienteEvolucionBFecha = '1000-01-01 00:00:00'
         LIMIT 1) AS id_cirujano
    FROM pacienteevolucion pe
    JOIN persona pac ON pac.PersonaNumero = pe.PersonaNumero
    WHERE pe.PacienteEvolucionGestion = {gestion}
      AND pe.PacienteEvolucionNroInter = {internacion}
      AND pe.PacienteEvolucionSector = -1
      AND pe.PacienteEvolucionTipo IN (7, 8, 9, 10, 11, 12, 13)
      AND pe.PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    GROUP BY pe.PersonaNumero, pe.PacienteEvolucionNroIntId, pac.PersonaNombreCompleto,
             pe.PacienteEvolucionGestion, pe.PacienteEvolucionNroInter
    LIMIT 1
    """
    results = _execute_query(query)
    if results and len(results) > 0:
        return results[0]
    return None


def obtener_detalle_cirugia(
    persona_numero: int, cuenta_gestion: int, cuenta_internacion: int, cuenta_id: int
) -> Optional[Dict[str, Any]]:
    """Obtiene el detalle completo de una cirugía (checklist OMS, informe quirúrgico, anestésico, etc.)."""
    query_template = _load_query("get_detalle_cirugia_v2")
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
