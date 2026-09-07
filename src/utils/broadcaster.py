import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime


class NotificationBroadcaster:
    """
    Gestor central de distribución en tiempo real (Pub/Sub) para Server-Sent Events (SSE).
    Mantiene las conexiones activas de los usuarios en la plataforma y entrega las
    notificaciones en caliente según los destinatarios correspondientes.
    """

    def __init__(self):
        # connection_id -> { "queue": asyncio.Queue, "user_id": int, "id_rol": int, "rol": str }
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Registra el event loop principal de FastAPI/Uvicorn."""
        self._loop = loop

    def get_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        if self._loop and self._loop.is_running():
            return self._loop
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return None

    def register(self, connection_id: str, queue: asyncio.Queue, user_id: Optional[int] = None, id_rol: Optional[int] = None, rol: Optional[str] = None):
        """Registra una nueva conexión SSE para un cliente autenticado."""
        if not self._loop:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

        self._connections[connection_id] = {
            "queue": queue,
            "user_id": int(user_id) if user_id is not None else None,
            "id_rol": int(id_rol) if id_rol is not None else None,
            "rol": (rol or "").strip().upper() if rol else None,
            "connected_at": datetime.now()
        }
        print(f"[SSE] Conexión abierta: id={connection_id} (usuario={user_id}, rol={id_rol} - {rol}). Total conexiones: {len(self._connections)}")

    def unregister(self, connection_id: str):
        """Elimina una conexión SSE cerrada."""
        if connection_id in self._connections:
            info = self._connections.pop(connection_id)
            print(f"[SSE] Conexión cerrada: id={connection_id} (usuario={info.get('user_id')}). Conexiones restantes: {len(self._connections)}")

    def _es_destinatario(
        self,
        conn_info: Dict[str, Any],
        target_user_id: Optional[int] = None,
        target_role_id: Optional[int] = None,
        target_roles_ids: Optional[List[int]] = None,
        target_users_ids: Optional[List[int]] = None,
        broadcast_all: bool = False
    ) -> bool:
        """Determina si una conexión específica debe recibir el mensaje."""
        if broadcast_all:
            return True

        c_user = conn_info.get("user_id")
        c_rol = conn_info.get("id_rol")
        c_rol_nombre = conn_info.get("rol")

        # SuperAdmin siempre recibe las notificaciones operativas del sistema
        if c_rol_nombre == "SUPERADMIN":
            return True

        # Destinatario usuario específico
        if target_user_id is not None and c_user is not None and int(c_user) == int(target_user_id):
            return True

        # Lista de usuarios específicos
        if target_users_ids and c_user is not None:
            if any(int(c_user) == int(u_id) for u_id in target_users_ids if u_id is not None):
                return True

        # Destinatario rol específico
        if target_role_id is not None and c_rol is not None and int(c_rol) == int(target_role_id):
            return True

        # Lista de roles específicos
        if target_roles_ids and c_rol is not None:
            if any(int(c_rol) == int(r_id) for r_id in target_roles_ids if r_id is not None):
                return True

        # Si no se especificó ningún destinatario concreto, se asume broadcast general
        if target_user_id is None and target_role_id is None and not target_roles_ids and not target_users_ids:
            return True

        return False

    async def broadcast_async(
        self,
        event_type: str,
        data: Dict[str, Any],
        target_user_id: Optional[int] = None,
        target_role_id: Optional[int] = None,
        target_roles_ids: Optional[List[int]] = None,
        target_users_ids: Optional[List[int]] = None,
        broadcast_all: bool = False
    ):
        """Envía de forma asíncrona un evento a todas las conexiones que cumplan el filtro."""
        if not self._connections:
            return

        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        mensaje_sse = f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

        desconectados = []
        enviados = 0

        for conn_id, conn_info in list(self._connections.items()):
            if self._es_destinatario(
                conn_info,
                target_user_id=target_user_id,
                target_role_id=target_role_id,
                target_roles_ids=target_roles_ids,
                target_users_ids=target_users_ids,
                broadcast_all=broadcast_all
            ):
                try:
                    queue: asyncio.Queue = conn_info["queue"]
                    queue.put_nowait(mensaje_sse)
                    enviados += 1
                except asyncio.QueueFull:
                    desconectados.append(conn_id)
                except Exception as e:
                    print(f"⚠️ Error enviando a conexión {conn_id}: {e}")
                    desconectados.append(conn_id)

        for conn_id in desconectados:
            self.unregister(conn_id)

        if enviados > 0:
            print(f"[SSE EN CALIENTE] Evento '{event_type}' entregado a {enviados} cliente(s) en vivo.")

    def broadcast_sync(
        self,
        event_type: str,
        data: Dict[str, Any],
        target_user_id: Optional[int] = None,
        target_role_id: Optional[int] = None,
        target_roles_ids: Optional[List[int]] = None,
        target_users_ids: Optional[List[int]] = None,
        broadcast_all: bool = False
    ):
        """
        Método seguro para emitir eventos desde hilos o funciones síncronas.
        """
        loop = self.get_loop()
        if loop and loop.is_running():
            try:
                current_loop = None
                try:
                    current_loop = asyncio.get_running_loop()
                except RuntimeError:
                    pass

                if current_loop is loop:
                    asyncio.create_task(
                        self.broadcast_async(
                            event_type, data,
                            target_user_id=target_user_id,
                            target_role_id=target_role_id,
                            target_roles_ids=target_roles_ids,
                            target_users_ids=target_users_ids,
                            broadcast_all=broadcast_all
                        )
                    )
                else:
                    asyncio.run_coroutine_threadsafe(
                        self.broadcast_async(
                            event_type, data,
                            target_user_id=target_user_id,
                            target_role_id=target_role_id,
                            target_roles_ids=target_roles_ids,
                            target_users_ids=target_users_ids,
                            broadcast_all=broadcast_all
                        ),
                        loop
                    )
            except Exception as e:
                print(f"⚠️ Error al enviar broadcast_sync: {e}")

    def notificar_nueva(
        self,
        notificacion: Dict[str, Any],
        target_user_id: Optional[int] = None,
        target_role_id: Optional[int] = None,
        target_roles_ids: Optional[List[int]] = None,
        target_users_ids: Optional[List[int]] = None,
        broadcast_all: bool = False
    ):
        """Emite una nueva notificación en caliente."""
        self.broadcast_sync(
            event_type="nueva_notificacion",
            data=notificacion,
            target_user_id=target_user_id,
            target_role_id=target_role_id,
            target_roles_ids=target_roles_ids,
            target_users_ids=target_users_ids,
            broadcast_all=broadcast_all
        )

    def notificar_leidas(
        self,
        id_usuario: Optional[int] = None,
        id_rol: Optional[int] = None,
        id_notificacion: Optional[int] = None,
        todas: bool = False
    ):
        """Sincroniza en tiempo real cuando se leen notificaciones."""
        self.broadcast_sync(
            event_type="notificaciones_leidas",
            data={
                "id_notificacion": id_notificacion,
                "todas": todas,
                "id_usuario": id_usuario,
                "id_rol": id_rol
            },
            target_user_id=id_usuario,
            target_role_id=id_rol
        )

    def notificar_cambio_solicitud(
        self,
        codigo_solicitud: str,
        nuevo_estado: str,
        detalle: Optional[str] = None,
        target_user_id: Optional[int] = None,
        target_role_id: Optional[int] = None
    ):
        """Notifica cambio de estado en una solicitud para refrescar tablas/dashboard en caliente."""
        self.broadcast_sync(
            event_type="solicitud_actualizada",
            data={
                "codigo": codigo_solicitud,
                "estado": nuevo_estado,
                "detalle": detalle
            },
            target_user_id=target_user_id,
            target_role_id=target_role_id,
            broadcast_all=(target_user_id is None and target_role_id is None)
        )


notification_broadcaster = NotificationBroadcaster()
