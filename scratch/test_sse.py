import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
import json
from src.utils.security import create_access_token
from src.utils.broadcaster import notification_broadcaster
from datetime import timedelta

async def test_broadcaster():
    print("Iniciando prueba unitaria de NotificationBroadcaster...")
    
    # Simular una cola SSE para un usuario ID 10 con Rol ID 3 (SST)
    queue = asyncio.Queue()
    conn_id = "test-conn-1"
    notification_broadcaster.register(
        connection_id=conn_id,
        queue=queue,
        user_id=10,
        id_rol=3,
        rol="SST"
    )

    # 1. Probar emisión dirigida a rol 3
    test_notif = {
        "id": 999,
        "titulo": "Prueba Dictamen SST",
        "mensaje": "Se requiere revisión en caliente",
        "tipo": "info",
        "enlace": "/solicitudes/revision/RAD-TEST01"
    }

    notification_broadcaster.notificar_nueva(test_notif, target_role_id=3)
    
    # Leer de la cola
    msg = await asyncio.wait_for(queue.get(), timeout=2.0)
    print("Mensaje recibido para rol 3:")
    print(msg)
    assert "event: nueva_notificacion" in msg
    assert "Prueba Dictamen SST" in msg

    # 2. Probar emisión a otro rol (Rol 2 - Gestion Documental) -> No debe llegar a la cola
    notification_broadcaster.notificar_nueva(
        {"id": 1000, "titulo": "Aviso solo para GD"},
        target_role_id=2
    )

    try:
        msg_no = await asyncio.wait_for(queue.get(), timeout=0.5)
        raise AssertionError("Error: No debió llegar un mensaje dirigido a otro rol!")
    except asyncio.TimeoutError:
        print("OK: El mensaje para otro rol no fue entregado a este cliente (filtrado correcto).")

    # 3. Probar emisión global (broadcast_all=True)
    notification_broadcaster.notificar_nueva(
        {"id": 1001, "titulo": "Comunicado General SuperAdmin", "mensaje": "Mantenimiento"},
        broadcast_all=True
    )
    msg_broadcast = await asyncio.wait_for(queue.get(), timeout=2.0)
    print("Mensaje de broadcast recibido:")
    print(msg_broadcast)
    assert "Comunicado General SuperAdmin" in msg_broadcast

    # 4. Probar cambio de solicitud en caliente
    notification_broadcaster.notificar_cambio_solicitud(
        codigo_solicitud="RAD-TEST01",
        nuevo_estado="POR APROBAR"
    )
    msg_cambio = await asyncio.wait_for(queue.get(), timeout=2.0)
    print("Mensaje de cambio de solicitud recibido:")
    print(msg_cambio)
    assert "event: solicitud_actualizada" in msg_cambio

    # Limpiar conexión
    notification_broadcaster.unregister(conn_id)
    print("[OK] Todas las validaciones de NotificationBroadcaster pasaron satisfactoriamente!")

if __name__ == "__main__":
    asyncio.run(test_broadcaster())
