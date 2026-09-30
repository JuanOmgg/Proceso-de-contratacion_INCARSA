from database import GET_conexion
from typing import List, Dict, Any
from datetime import datetime

def GENERAR_RADICADO_CORRESPONDENCIA(cursor, anio: int) -> str:
    """
    Genera un radicado consecutivo tipo SCR-001, SCR-002...
    El consecutivo se reinicia cada nuevo año desde 001.
    """
    cursor.execute("""
        SELECT MAX(CAST(SUBSTRING(radicado, 5) AS UNSIGNED)) AS max_num 
        FROM correspondencia 
        WHERE YEAR(fecha_envio) = %s AND radicado LIKE %s
    """, (anio, "SCR-%"))
    row = cursor.fetchone()
    max_num = row.get("max_num") if row else None
    if max_num is None or not max_num:
        consecutivo = 1
    else:
        consecutivo = int(max_num) + 1
    return f"SCR-{str(consecutivo).zfill(3)}"


def CREATE_correspondencia_db(correspondencia: Dict) -> Dict:
    
    try:

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                fecha_envio = correspondencia.get("fecha_envio")
                if not fecha_envio:
                    fecha_envio = datetime.now().strftime("%Y-%m-%d")

                try:
                    anio = int(str(fecha_envio).split("-")[0])
                except Exception:
                    anio = datetime.now().year

                # Generar o validar radicado consecutivo
                radicado = correspondencia.get("radicado")
                if radicado:
                    radicado = str(radicado).strip().upper()
                    cursor.execute("SELECT id FROM correspondencia WHERE UPPER(radicado) = %s", (radicado,))
                    if cursor.fetchone():
                        return {
                            "exito": False,
                            "mensaje": f"El código de radicado '{radicado}' ya existe en el sistema."
                        }
                else:
                    radicado = GENERAR_RADICADO_CORRESPONDENCIA(cursor, anio)

                sql_corr = """
                    INSERT INTO correspondencia (
                        radicado,
                        tipo_correspondencia,
                        asunto,
                        procedencia,
                        destino,
                        fecha_envio
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """
                val_corr = (
                    radicado,
                    correspondencia.get("tipo_correspondencia", ""),
                    correspondencia.get("asunto", ""),
                    correspondencia.get("procedencia", ""),
                    correspondencia.get("destino", ""),
                    fecha_envio,
                )

                cursor.execute(sql_corr, val_corr)
                id_corr = cursor.lastrowid

                conexion.commit()

        return {
            "exito": True,
            "mensaje": "✅✅ Correspondencia creada exitosamente. ✅✅",
            "id_generado": id_corr,
            "radicado": radicado,
        }

    except Exception as e:
        print(f"❌❌ Error al intentar guardar correspondencia en la base de datos: {e}. ❌❌")
        return {
            "exito": False,
            "mensaje": f"❌❌ Error en la base de datos : {e} ❌❌",
        }

def GET_correspondencia_db(identificador: Any) -> Dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                # Si es un ID numérico
                if str(identificador).strip().isdigit():
                    sql = """
                        SELECT 
                            id,
                            radicado,
                            tipo_correspondencia,
                            asunto,
                            procedencia,
                            destino,
                            fecha_envio
                        FROM correspondencia
                        WHERE id = %s
                    """
                    cursor.execute(sql, (int(identificador),))
                else:
                    # Búsqueda por radicado exacto, asunto, procedencia o destino
                    term = str(identificador).strip()
                    sql = """
                        SELECT 
                            id,
                            radicado,
                            tipo_correspondencia,
                            asunto,
                            procedencia,
                            destino,
                            fecha_envio
                        FROM correspondencia
                        WHERE LOWER(radicado) = LOWER(%s)
                           OR LOWER(asunto) LIKE LOWER(%s)
                           OR LOWER(procedencia) LIKE LOWER(%s)
                           OR LOWER(destino) LIKE LOWER(%s)
                        LIMIT 1
                    """
                    cursor.execute(sql, (term, f"%{term}%", f"%{term}%", f"%{term}%"))

                item = cursor.fetchone()

                if not item:
                    return {
                        "exito": False,
                        "mensaje": f"❌❌ Correspondencia con identificador '{identificador}' no fue encontrada. ❌❌",
                    }

                # Formatear fecha si es objeto datetime para serialización segura
                if item.get("fecha_envio") and isinstance(item["fecha_envio"], datetime):
                    item["fecha_envio"] = item["fecha_envio"].isoformat()

                return {
                    "exito": True,
                    "data": item
                }

    except Exception as e:
        print(f"❌❌ Error al consultar correspondencia en la BD: {e} ❌❌")
        return {
            "exito": False,
            "mensaje": f"❌❌ Error en la base de datos: {e} ❌❌",
        }

def GET_ALL_correspondencia_db() -> Dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                sql = """
                    SELECT 
                        id,
                        radicado,
                        tipo_correspondencia,
                        asunto,
                        procedencia,
                        destino,
                        fecha_envio
                    FROM correspondencia
                    ORDER BY id DESC
                """
                cursor.execute(sql)
                lista = cursor.fetchall() or []

                for item in lista:
                    if item.get("fecha_envio") and isinstance(item["fecha_envio"], datetime):
                        item["fecha_envio"] = item["fecha_envio"].isoformat()

                return {
                    "exito": True,
                    "data": lista,
                    "total": len(lista)
                }

    except Exception as e:
        print(f"❌❌ Error al consultar lista de correspondencia en la BD: {e} ❌❌")
        return {
            "exito": False,
            "mensaje": f"❌❌ Error en la base de datos: {e} ❌❌",
            "data": []
        }

def DELETE_correspondencia_db(identificador: Any) -> Dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                sql = """
                    DELETE FROM correspondencia
                    WHERE id = %s
                """
                cursor.execute(sql, (int(identificador),))
                conexion.commit()

                return {
                    "exito": True,
                    "mensaje": "✅✅ Correspondencia eliminada exitosamente. ✅✅",
                }

    except Exception as e:
        print(f"❌❌ Error al eliminar correspondencia en la base de datos: {e}. ❌❌")
        return {
            "exito": False,
            "mensaje": f"❌❌ Error en la base de datos: {e} ❌❌",
        }


def UPDATE_correspondencia_db(id_corr: int, correspondencia: Dict) -> Dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                campos = []
                valores = []

                if "radicado" in correspondencia and correspondencia["radicado"]:
                    rad_up = str(correspondencia["radicado"]).strip().upper()
                    cursor.execute("SELECT id FROM correspondencia WHERE UPPER(radicado) = %s AND id != %s", (rad_up, int(id_corr)))
                    if cursor.fetchone():
                        return {
                            "exito": False,
                            "mensaje": f"El código de radicado '{rad_up}' ya pertenece a otra correspondencia."
                        }

                for k, col in [
                    ("tipo_correspondencia", "tipo_correspondencia"),
                    ("asunto", "asunto"),
                    ("procedencia", "procedencia"),
                    ("destino", "destino"),
                    ("fecha_envio", "fecha_envio"),
                    ("radicado", "radicado"),
                ]:
                    if k in correspondencia and correspondencia[k] is not None:
                        campos.append(f"{col} = %s")
                        valores.append(correspondencia[k])

                if not campos:
                    return {
                        "exito": True,
                        "mensaje": "No se proporcionaron campos para actualizar.",
                    }

                valores.append(int(id_corr))
                sql = f"UPDATE correspondencia SET {', '.join(campos)} WHERE id = %s"
                cursor.execute(sql, tuple(valores))
                conexion.commit()

                return {
                    "exito": True,
                    "mensaje": "✅✅ Correspondencia actualizada exitosamente. ✅✅",
                }

    except Exception as e:
        print(f"❌❌ Error al actualizar correspondencia en la base de datos: {e}. ❌❌")
        return {
            "exito": False,
            "mensaje": f"❌❌ Error en la base de datos: {e} ❌❌",
        }