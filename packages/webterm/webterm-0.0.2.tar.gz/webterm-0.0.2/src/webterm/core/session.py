"""Session management for webterm."""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional

from webterm.core.config import settings
from webterm.core.pty_manager import PTYManager
from webterm.logger import get_logger

logger = get_logger("session")


@dataclass
class Session:
    """Represents a terminal session."""

    id: str
    pty: PTYManager
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def is_expired(self, timeout: int) -> bool:
        """Check if session has expired.

        Args:
            timeout: Timeout in seconds

        Returns:
            True if expired, False otherwise
        """
        return time.time() - self.last_activity > timeout


class SessionManager:
    """Manages terminal sessions."""

    def __init__(
        self,
        max_sessions: int = settings.max_sessions,
        session_timeout: int = settings.session_timeout,
    ):
        """Initialize session manager.

        Args:
            max_sessions: Maximum concurrent sessions
            session_timeout: Session timeout in seconds
        """
        self._sessions: Dict[str, Session] = {}
        self._max_sessions = max_sessions
        self._session_timeout = session_timeout
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    @property
    def session_count(self) -> int:
        """Get current session count."""
        return len(self._sessions)

    async def create_session(self, shell: Optional[str] = None) -> Optional[Session]:
        """Create a new terminal session.

        Args:
            shell: Optional shell path override

        Returns:
            New session or None if limit reached
        """
        async with self._lock:
            if len(self._sessions) >= self._max_sessions:
                logger.warning(f"Session limit reached ({self._max_sessions})")
                return None

            session_id = str(uuid.uuid4())
            shell_path = shell or settings.get_shell()
            pty = PTYManager(shell=shell_path)

            if not await pty.spawn():
                logger.error("Failed to spawn PTY for session")
                return None

            session = Session(id=session_id, pty=pty)
            self._sessions[session_id] = session
            logger.info(f"Created session {session_id}")
            return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session or None if not found
        """
        session = self._sessions.get(session_id)
        if session:
            session.touch()
        return session

    async def remove_session(self, session_id: str) -> bool:
        """Remove and terminate a session.

        Args:
            session_id: Session ID

        Returns:
            True if removed, False if not found
        """
        async with self._lock:
            session = self._sessions.pop(session_id, None)
            if session:
                await session.pty.terminate()
                logger.info(f"Removed session {session_id}")
                return True
            return False

    async def cleanup_expired(self) -> int:
        """Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired = []
        for session_id, session in self._sessions.items():
            if session.is_expired(self._session_timeout):
                expired.append(session_id)

        for session_id in expired:
            await self.remove_session(session_id)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

        return len(expired)

    async def start_cleanup_task(self, interval: int = 60) -> None:
        """Start periodic cleanup task.

        Args:
            interval: Cleanup interval in seconds
        """

        async def cleanup_loop():
            while True:
                await asyncio.sleep(interval)
                await self.cleanup_expired()

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.debug("Started session cleanup task")

    async def stop_cleanup_task(self) -> None:
        """Stop the cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.debug("Stopped session cleanup task")

    async def shutdown(self) -> None:
        """Shutdown all sessions and cleanup."""
        await self.stop_cleanup_task()

        async with self._lock:
            for session_id in list(self._sessions.keys()):
                session = self._sessions.pop(session_id)
                await session.pty.terminate()

        logger.info("Session manager shutdown complete")


# Global session manager instance
session_manager = SessionManager()
