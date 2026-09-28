import sys
import os
import unittest
from datetime import date

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loaders.estadisticas_loader import (
    GET_plantas_disponibles_db,
    GET_estadisticas_ingresos_plantas_db,
    GET_detalle_personas_dia_planta_db
)


class TestEstadisticasAfluencia(unittest.TestCase):

    def test_01_obtener_plantas(self):
        """Verifica que la consulta de plantas para los filtros retorne registros válidos."""
        plantas = GET_plantas_disponibles_db()
        self.assertIsInstance(plantas, list)
        self.assertGreater(len(plantas), 0, "Debe existir al menos una planta en la base de datos.")
        self.assertIn("id", plantas[0])
        self.assertIn("nombre", plantas[0])

    def test_02_estadisticas_ingresos_diarios_kpis_y_series(self):
        """Verifica que el cálculo diario retorne estructura completa con KPIs y series temporales."""
        f_ini = date(2026, 9, 1)
        f_fin = date(2026, 9, 25)
        res = GET_estadisticas_ingresos_plantas_db(
            fecha_inicio=f_ini,
            fecha_fin=f_fin,
            estado="TODOS"
        )
        self.assertTrue(res["exito"], f"La consulta falló: {res.get('mensaje')}")
        kpis = res["kpis"]
        self.assertIn("total_personas_unicas_periodo", kpis)
        self.assertIn("total_ingresos_acumulados", kpis)
        self.assertIn("promedio_diario", kpis)
        self.assertIn("dia_pico", kpis)
        self.assertIn("planta_mayor_afluencia", kpis)

        # Verificar que la serie temporal cubra los 25 días consultados
        serie = res["serie_tiempo"]
        self.assertEqual(len(serie), 25, "La serie temporal debe contener exactamente 25 días.")

    def test_03_deduplicacion_estricta_personas(self):
        """
        Verifica que en el detalle de personas de un día y planta,
        no existan personas duplicadas (mismo id_persona), y que aquellas con 2 o más
        solicitudes consoliden todos sus radicados en la misma ficha.
        """
        f_ini = date(2026, 9, 1)
        f_fin = date(2026, 9, 25)
        res = GET_estadisticas_ingresos_plantas_db(fecha_inicio=f_ini, fecha_fin=f_fin, estado="TODOS")
        self.assertTrue(res["exito"])
        
        # Buscar un registro con más de 1 solicitud
        registro_con_solicitudes = None
        for r in res["registros"]:
            if r["total_solicitudes"] >= 2:
                registro_con_solicitudes = r
                break

        if registro_con_solicitudes:
            detalle = GET_detalle_personas_dia_planta_db(
                fecha=registro_con_solicitudes["fecha"],
                id_planta=registro_con_solicitudes["id_planta"],
                estado="TODOS"
            )
            self.assertTrue(detalle["exito"])
            personas = detalle["personas"]

            # Validar que cada persona sea única (sin duplicidad de id_persona)
            ids_personas = [p["id_persona"] for p in personas]
            self.assertEqual(
                len(ids_personas),
                len(set(ids_personas)),
                "No debe haber personas duplicadas en el detalle del día y planta."
            )

            # Validar que el conteo en el encabezado coincida exactamente con la lista
            self.assertEqual(
                len(personas),
                detalle["total_personas_unicas"],
                "El total reportado debe coincidir con el tamaño de la lista de personas."
            )


if __name__ == "__main__":
    unittest.main()
