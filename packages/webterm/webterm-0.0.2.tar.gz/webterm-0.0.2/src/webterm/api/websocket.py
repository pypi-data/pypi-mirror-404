"""WebSocket connection manager for webterm."""

import asyncio
import json
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from webterm.core.session import Session, session_manager
from webterm.core.stats import get_system_stats
from webterm.logger import get_logger

logger = get_logger("websocket")

STATS_INTERVAL = 2.0  # seconds between stats updates


class WebSocketManager:
    """Manages WebSocket connections and bridges them to PTY sessions."""

    def __init__(self):
        """Initialize the WebSocket manager."""
        self._detailed_stats: dict[WebSocket, bool] = {}

    async def handle_connection(self, websocket: WebSocket) -> None:
        """Handle a WebSocket connection.

        Args:
            websocket: The WebSocket connection
        """
        await websocket.accept()
        session: Optional[Session] = None

        try:
            # Create a new session
            session = await session_manager.create_session()
            if not session:
                await self._send_error(websocket, "Failed to create session (limit reached)")
                await websocket.close()
                return

            logger.info(f"WebSocket connected, session {session.id}")

            # Initialize detailed stats state for this connection
            self._detailed_stats[websocket] = False

            # Start reading from PTY and forwarding to WebSocket
            read_task = asyncio.create_task(self._read_pty_loop(websocket, session))
            # Start sending system stats periodically
            stats_task = asyncio.create_task(self._stats_loop(websocket))

            try:
                # Handle incoming WebSocket messages
                await self._handle_messages(websocket, session)
            finally:
                read_task.cancel()
                stats_task.cancel()
                try:
                    await read_task
                except asyncio.CancelledError:
                    pass
                try:
                    await stats_task
                except asyncio.CancelledError:
                    pass

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await self._send_error(websocket, str(e))
        finally:
            # Clean up detailed stats state
            self._detailed_stats.pop(websocket, None)
            if session:
                await session_manager.remove_session(session.id)

    async def _read_pty_loop(self, websocket: WebSocket, session: Session) -> None:
        """Read from PTY and send to WebSocket.

        Args:
            websocket: The WebSocket connection
            session: The terminal session
        """
        while session.pty.is_running:
            try:
                data = await session.pty.read()
                if data:
                    await self._send_output(websocket, data.decode("utf-8", errors="replace"))
                else:
                    await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"PTY read error: {e}")
                break

        await self._send_error(websocket, "Session terminated")

    async def _handle_messages(self, websocket: WebSocket, session: Session) -> None:
        """Handle incoming WebSocket messages.

        Args:
            websocket: The WebSocket connection
            session: The terminal session
        """
        while True:
            try:
                raw = await websocket.receive_text()
                message = json.loads(raw)
                msg_type = message.get("type")

                if msg_type == "input":
                    data = message.get("data", "")
                    await session.pty.write(data.encode("utf-8"))
                    session.touch()

                elif msg_type == "resize":
                    rows = message.get("rows", 24)
                    cols = message.get("cols", 80)
                    session.pty.resize(rows, cols)
                    session.touch()

                elif msg_type == "stats_detail":
                    # Toggle or set detailed stats mode
                    enabled = message.get("enabled")
                    if enabled is None:
                        # Toggle
                        self._detailed_stats[websocket] = not self._detailed_stats.get(websocket, False)
                    else:
                        self._detailed_stats[websocket] = bool(enabled)
                    # Send immediate stats update with new detail level
                    await self._send_stats(websocket)

                elif msg_type == "get_cwd":
                    # Get current working directory of the terminal
                    cwd = session.pty.get_cwd()
                    await websocket.send_json({"type": "cwd", "path": cwd})

                else:
                    logger.warning(f"Unknown message type: {msg_type}")

            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.error(f"Message handling error: {e}")

    async def _send_output(self, websocket: WebSocket, data: str) -> None:
        """Send terminal output to WebSocket.

        Args:
            websocket: The WebSocket connection
            data: Output data to send
        """
        try:
            await websocket.send_json({"type": "output", "data": data})
        except Exception:
            pass

    async def _send_error(self, websocket: WebSocket, message: str) -> None:
        """Send error message to WebSocket.

        Args:
            websocket: The WebSocket connection
            message: Error message
        """
        try:
            await websocket.send_json({"type": "error", "message": message})
        except Exception:
            pass

    async def _stats_loop(self, websocket: WebSocket) -> None:
        """Send system stats periodically.

        Args:
            websocket: The WebSocket connection
        """
        while True:
            try:
                await self._send_stats(websocket)
                await asyncio.sleep(STATS_INTERVAL)
            except Exception:
                break

    async def _send_stats(self, websocket: WebSocket) -> None:
        """Send system stats to WebSocket.

        Args:
            websocket: The WebSocket connection
        """
        try:
            detailed = self._detailed_stats.get(websocket, False)
            stats = get_system_stats(detailed=detailed)
            await websocket.send_json({"type": "stats", **stats})
        except Exception:
            pass


# Global WebSocket manager instance
ws_manager = WebSocketManager()
