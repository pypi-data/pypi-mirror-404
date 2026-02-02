"""PTY (pseudo-terminal) manager for webterm."""

import asyncio
import fcntl
import os
import pty
import signal
import struct
import termios
from typing import Callable, Optional

from webterm.logger import get_logger

logger = get_logger("pty_manager")


class PTYManager:
    """Manages a pseudo-terminal for shell interaction."""

    def __init__(self, shell: str = "/bin/bash"):
        """Initialize PTY manager.

        Args:
            shell: Path to shell executable
        """
        self.shell = shell
        self.pid: Optional[int] = None
        self.fd: Optional[int] = None
        self._running = False
        self._read_task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        """Check if the PTY process is running."""
        return self._running and self.pid is not None

    async def spawn(self) -> bool:
        """Spawn a new PTY process.

        Returns:
            True if successful, False otherwise
        """
        if self._running:
            logger.warning("PTY already running")
            return False

        try:
            self.pid, self.fd = pty.fork()

            if self.pid == 0:
                # Child process - set up environment and exec the shell
                home = os.path.expanduser("~")
                os.chdir(home)
                # Set TERM for proper color and feature support
                os.environ["TERM"] = "xterm-256color"
                os.environ["COLORTERM"] = "truecolor"
                os.execvp(self.shell, [self.shell])
            else:
                # Parent process
                self._running = True
                # Set non-blocking mode
                flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
                fcntl.fcntl(self.fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                logger.info(f"Spawned PTY with PID {self.pid}")
                return True

        except Exception as e:
            logger.error(f"Failed to spawn PTY: {e}")
            self._running = False
            return False

        return False

    async def read(self, size: int = 4096) -> Optional[bytes]:
        """Read data from the PTY.

        Args:
            size: Maximum bytes to read

        Returns:
            Bytes read or None if no data/error
        """
        if not self._running or self.fd is None:
            return None

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, self._blocking_read, size)
            return data
        except Exception:
            return None

    def _blocking_read(self, size: int) -> Optional[bytes]:
        """Blocking read from PTY fd."""
        try:
            return os.read(self.fd, size)
        except (OSError, BlockingIOError):
            return None

    async def write(self, data: bytes) -> bool:
        """Write data to the PTY.

        Args:
            data: Bytes to write

        Returns:
            True if successful, False otherwise
        """
        if not self._running or self.fd is None:
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, os.write, self.fd, data)
            return True
        except Exception as e:
            logger.error(f"Failed to write to PTY: {e}")
            return False

    def resize(self, rows: int, cols: int) -> bool:
        """Resize the PTY window.

        Args:
            rows: Number of rows
            cols: Number of columns

        Returns:
            True if successful, False otherwise
        """
        if not self._running or self.fd is None:
            return False

        try:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
            logger.debug(f"Resized PTY to {rows}x{cols}")
            return True
        except Exception as e:
            logger.error(f"Failed to resize PTY: {e}")
            return False

    def get_cwd(self) -> str:
        """Get the current working directory of the PTY process.

        Returns:
            Current working directory path, or home directory if unable to determine
        """
        if not self._running or self.pid is None:
            return os.path.expanduser("~")

        try:
            # Try Linux /proc filesystem first
            proc_cwd = f"/proc/{self.pid}/cwd"
            if os.path.exists(proc_cwd):
                return os.readlink(proc_cwd)
        except (OSError, PermissionError):
            pass

        try:
            # Try macOS lsof approach
            import subprocess

            result = subprocess.run(
                ["lsof", "-p", str(self.pid), "-Fn"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("n") and line.endswith("cwd"):
                        continue
                    if line.startswith("n/"):
                        # Found a path, check if it's the cwd
                        path = line[1:]  # Remove 'n' prefix
                        if os.path.isdir(path):
                            return path
        except Exception:
            pass

        # Fallback: try to get cwd from /dev/fd
        try:
            import subprocess

            result = subprocess.run(
                ["pwdx", str(self.pid)],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if result.returncode == 0:
                # Output format: "PID: /path/to/cwd"
                parts = result.stdout.strip().split(": ", 1)
                if len(parts) == 2:
                    return parts[1]
        except Exception:
            pass

        return os.path.expanduser("~")

    async def terminate(self, timeout: float = 5.0) -> bool:
        """Terminate the PTY process gracefully.

        Uses SIGHUP -> SIGTERM -> SIGKILL escalation.

        Args:
            timeout: Seconds to wait between signals

        Returns:
            True if terminated, False otherwise
        """
        if not self._running or self.pid is None:
            return True

        self._running = False

        try:
            # Try SIGHUP first
            os.kill(self.pid, signal.SIGHUP)
            if await self._wait_for_exit(timeout / 3):
                return True

            # Try SIGTERM
            os.kill(self.pid, signal.SIGTERM)
            if await self._wait_for_exit(timeout / 3):
                return True

            # Force SIGKILL
            os.kill(self.pid, signal.SIGKILL)
            await self._wait_for_exit(timeout / 3)

        except ProcessLookupError:
            # Process already gone
            pass
        except Exception as e:
            logger.error(f"Error terminating PTY: {e}")

        # Close file descriptor
        if self.fd is not None:
            try:
                os.close(self.fd)
            except Exception:
                pass
            self.fd = None

        self.pid = None
        logger.info("PTY terminated")
        return True

    async def _wait_for_exit(self, timeout: float) -> bool:
        """Wait for process to exit.

        Args:
            timeout: Seconds to wait

        Returns:
            True if process exited, False if still running
        """
        try:
            for _ in range(int(timeout * 10)):
                pid, _ = os.waitpid(self.pid, os.WNOHANG)
                if pid != 0:
                    return True
                await asyncio.sleep(0.1)
        except ChildProcessError:
            return True
        return False

    async def start_reading(self, callback: Callable[[bytes], None]) -> None:
        """Start continuous reading from PTY and call callback with data.

        Args:
            callback: Function to call with read data
        """
        while self._running and self.fd is not None:
            try:
                data = await self.read()
                if data:
                    callback(data)
                else:
                    await asyncio.sleep(0.01)
            except Exception:
                break
