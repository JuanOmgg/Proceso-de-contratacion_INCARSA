import unittest
from datetime import datetime, timedelta
from database import GET_conexion
from src.loaders.solicitudes_loaders import (
    CREATE_token_formulario_db,
    GET_token_formulario_db,
    LISTAR_tokens_formulario_db,
    REVOCAR_token_formulario_db,
    MARCAR_token_usado_db,
    APROBAR_envio_solicitud_db,
    CREATE_solicitud_bd,
    GET_solicitud_bd,
    GET_ALL_solicitudes_bd
)

class TestFormularioTemporal(unittest.TestCase):
    def setUp(self):
        self.solicitante_id = 2  # Usuario con rol Solicitante / Gestion Documental
        self.admin_id = 1

    def test_01_crear_y_validar_token(self):
        res = CREATE_token_formulario_db(
            id_usuario=self.solicitante_id,
            duracion_horas=12.0,
            destinatario_nombre="Contratista Demo S.A.S.",
            destinatario_email="demo@contratista.com"
        )
        self.assertTrue(res.get("exito"))
        token = res["datos"]["token"]
        self.assertTrue(token)

        # Validar token
        info = GET_token_formulario_db(token)
        self.assertTrue(info.get("valido"))
        self.assertEqual(info.get("destinatario_nombre"), "Contratista Demo S.A.S.")
        self.assertIn("empresas", info.get("catalogos", {}))
        self.assertIn("contratistas", info.get("catalogos", {}))

    def test_02_revocar_token(self):
        res = CREATE_token_formulario_db(
            id_usuario=self.solicitante_id,
            duracion_horas=2.0
        )
        token_id = res["datos"]["id"]
        token = res["datos"]["token"]

        rev_res = REVOCAR_token_formulario_db(token_id=token_id, id_usuario=self.solicitante_id)
        self.assertTrue(rev_res.get("exito"))

        check = GET_token_formulario_db(token)
        self.assertFalse(check.get("valido"))
        self.assertIn("revocado", check.get("mensaje", "").lower())

    def test_03_flujo_pre_enviado_y_aprobacion(self):
        # 1. Crear token
        res_tok = CREATE_token_formulario_db(id_usuario=self.solicitante_id, duracion_horas=24.0)
        token = res_tok["datos"]["token"]

        # 2. Crear solicitud con estado PRE-ENVIADO
        payload = {
            "empresa_origen": 1,
            "empresa_contratista": 1,
            "tipo_personal": "Contratista",
            "nivel_riesgo": "MEDIO",
            "fecha_ingreso": datetime.now().strftime("%Y-%m-%d"),
            "fecha_salida": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "actividad": "Mantenimiento preventivo prueba pre-envío",
            "sub_plantas": [1],
            "id_usuario": self.solicitante_id,
            "diligenciado_por": self.solicitante_id,
            "estado": "PRE-ENVIADO",
            "personas": [
                {
                    "nombre": "Pedro",
                    "apellido": "Pérez",
                    "tipo_identificacion": "CC",
                    "identificacion": "1199887766",
                    "cargo": "Soldador",
                    "arl": "SURA",
                    "correo": "pedro.perez@testmail.com"
                }
            ],
            "vehiculos": []
        }

        res_create = CREATE_solicitud_bd(payload)
        self.assertTrue(res_create.get("exito"))
        sol_id = res_create.get("id_generado") or res_create.get("ids_generados")[0]
        cod = res_create.get("codigo") or res_create.get("codigos_generados")[0]

        # 3. Marcar token usado
        MARCAR_token_usado_db(token, sol_id)
        tok_check = GET_token_formulario_db(token)
        self.assertFalse(tok_check.get("valido"))

        # 4. Verificar que esté en PRE-ENVIADO
        sol_db = GET_solicitud_bd(sol_id)
        self.assertTrue(sol_db.get("exito"))
        self.assertEqual(sol_db["datos"]["estado"], "PRE-ENVIADO")

        # 4b. Verificar que se haya emitido notificación en base de datos para el Solicitante
        from src.loaders.notificacion_loader import obtener_notificaciones_db
        notifs = obtener_notificaciones_db(id_usuario=self.solicitante_id, limit=5)
        notif_match = next((n for n in notifs if cod in (n.get("mensaje") or "") or cod in (n.get("enlace") or "")), None)
        self.assertIsNotNone(notif_match)
        self.assertIn("PRE-ENVIADA", notif_match["mensaje"])

        # 5. Aprobar solicitud para que pase a ENVIADO
        res_aprob = APROBAR_envio_solicitud_db(sol_id, id_usuario=self.solicitante_id)
        self.assertTrue(res_aprob.get("exito"))

        sol_db_post = GET_solicitud_bd(sol_id)
        self.assertEqual(sol_db_post["datos"]["estado"], "ENVIADO")

    def test_04_guardar_persona_y_vehiculo_publico(self):
        from src.routes.solicitud_route import (
            GUARDAR_persona_formulario_temporal_rt,
            GUARDAR_vehiculo_formulario_temporal_rt
        )
        import random

        # 1. Crear token
        res_tok = CREATE_token_formulario_db(id_usuario=self.solicitante_id, duracion_horas=2.0)
        token = res_tok["datos"]["token"]

        # 2. Guardar persona con documentos
        rnd_doc = f"99{random.randint(100000, 999999)}"
        persona_payload = {
            "nombre": "Carlos",
            "apellido": "Gomez",
            "tipo_doc": "CC",
            "identificacion": rnd_doc,
            "cargo": "Supervisor HSE",
            "correo": f"carlos_{rnd_doc}@ejemplo.com",
            "observacion": "Prueba formulario público",
            "documentos": [
                {
                    "tipo_doc": "ARL",
                    "nombre_archivo": f"arl_{rnd_doc}.pdf",
                    "vigencia": "2026-12-31"
                },
                {
                    "tipo_doc": "Otro documento",
                    "tipo_doc_otro": "Certificado Alturas",
                    "nombre_archivo": f"alturas_{rnd_doc}.pdf",
                    "vigencia": "2027-01-15"
                }
            ]
        }
        res_per = GUARDAR_persona_formulario_temporal_rt(token=token, payload=persona_payload)
        self.assertTrue(res_per.get("exito"))
        self.assertIsNotNone(res_per.get("id"))
        p_data = res_per.get("persona", {})
        self.assertEqual(str(p_data.get("identificacion")), rnd_doc)

        # 3. Guardar vehículo con documentos
        rnd_placa = f"TST{random.randint(100, 999)}"
        vehiculo_payload = {
            "placa": rnd_placa,
            "tipo": "Camión",
            "conductor": "Carlos Gomez",
            "licencia_doc": f"licencia_{rnd_doc}.pdf",
            "documentos": [
                {
                    "tipo_doc": "SOAT",
                    "nombre_archivo": f"soat_{rnd_placa}.pdf"
                },
                {
                    "tipo_doc": "Revisión Tecnomecánica",
                    "nombre_archivo": f"tecno_{rnd_placa}.pdf"
                }
            ]
        }
        res_veh = GUARDAR_vehiculo_formulario_temporal_rt(token=token, payload=vehiculo_payload)
        self.assertTrue(res_veh.get("exito"))
        self.assertIsNotNone(res_veh.get("id"))
        v_data = res_veh.get("vehiculo", {})
        self.assertEqual(v_data.get("placa"), rnd_placa)


    def test_05_asignacion_empresa_contratista_en_solicitud(self):
        from src.routes.solicitud_route import ENVIAR_formulario_temporal_publico_rt
        from src.schemas.solicitud_schema import SolicitudInput

        # 1. Obtener una empresa contratista existente
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nombre, nit FROM emp_contratista LIMIT 1")
                contratista = cur.fetchone()

        self.assertIsNotNone(contratista)
        c_id = contratista["id"]
        c_nombre = contratista["nombre"]

        # 2. Crear token asignado a esta contratista
        res_tok = CREATE_token_formulario_db(
            id_usuario=self.solicitante_id,
            duracion_horas=24.0,
            id_empresa_contratista=c_id
        )
        self.assertTrue(res_tok.get("exito"))
        token = res_tok["datos"]["token"]

        # 3. Validar token público
        info = GET_token_formulario_db(token)
        self.assertTrue(info.get("valido"))
        self.assertEqual(info.get("id_empresa_contratista"), c_id)
        self.assertEqual(info.get("contratista_nombre"), c_nombre)

        # 4. Enviar formulario desde endpoint público
        payload = SolicitudInput(
            empresa_origen="1",
            empresa_contratista=c_id,
            tipo_personal="Contratista",
            nivel_riesgo="BAJO",
            fecha_ingreso=datetime.now().strftime("%Y-%m-%d"),
            fecha_salida=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            actividad="Mantenimiento contratista asignado",
            sub_plantas=[1]
        )
        res_envio = ENVIAR_formulario_temporal_publico_rt(token=token, payload=payload)
        self.assertTrue(res_envio.get("exito"))
        sol_id = res_envio.get("id_generado")
        self.assertIsNotNone(sol_id)

        # 5. Comprobar que en BD la solicitud tiene exactamente la empresa contratista asignada
        sol_db = GET_solicitud_bd(sol_id)
        self.assertTrue(sol_db.get("exito"))
        self.assertEqual(sol_db["datos"]["empresa_contratista"], c_id)


if __name__ == "__main__":
    unittest.main()

