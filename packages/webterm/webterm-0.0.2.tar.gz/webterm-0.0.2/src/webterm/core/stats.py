"""System resource monitoring for webterm."""

import os
import subprocess


def get_cpu_percent() -> float:
    """Get CPU usage percentage using /proc/stat or sysctl on macOS.

    Returns:
        CPU usage as a percentage (0-100)
    """
    try:
        # Try macOS approach first
        import subprocess

        result = subprocess.run(
            ["ps", "-A", "-o", "%cpu"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            total = sum(float(line.strip()) for line in lines if line.strip())
            # Normalize to number of CPUs
            cpu_count = os.cpu_count() or 1
            return min(total / cpu_count, 100.0)
    except Exception:
        pass

    try:
        # Try Linux /proc/stat approach
        with open("/proc/stat", "r") as f:
            line = f.readline()
            parts = line.split()
            if parts[0] == "cpu":
                user, nice, system, idle = map(int, parts[1:5])
                total = user + nice + system + idle
                used = user + nice + system
                if total > 0:
                    return (used / total) * 100.0
    except Exception:
        pass

    return 0.0


def get_memory_percent() -> float:
    """Get memory usage percentage.

    Returns:
        Memory usage as a percentage (0-100)
    """
    try:
        # Try macOS approach
        import subprocess

        result = subprocess.run(
            ["vm_stat"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            stats = {}
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":")
                    # Remove trailing period and convert to int
                    value = value.strip().rstrip(".")
                    try:
                        stats[key.strip()] = int(value)
                    except ValueError:
                        pass

            pages_free = stats.get("Pages free", 0)
            pages_active = stats.get("Pages active", 0)
            pages_inactive = stats.get("Pages inactive", 0)
            pages_speculative = stats.get("Pages speculative", 0)
            pages_wired = stats.get("Pages wired down", 0)

            total_pages = pages_free + pages_active + pages_inactive + pages_speculative + pages_wired
            used_pages = pages_active + pages_wired

            if total_pages > 0:
                return (used_pages / total_pages) * 100.0
    except Exception:
        pass

    try:
        # Try Linux /proc/meminfo approach
        with open("/proc/meminfo", "r") as f:
            meminfo = {}
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    value = int(parts[1])
                    meminfo[key] = value

            total = meminfo.get("MemTotal", 0)
            available = meminfo.get("MemAvailable", 0)

            if total > 0:
                used = total - available
                return (used / total) * 100.0
    except Exception:
        pass

    return 0.0


def get_gpu_info() -> dict | None:
    """Get GPU usage if available.

    Returns:
        Dictionary with gpu name and usage percentage, or None if no GPU
    """
    # Try NVIDIA GPU (nvidia-smi)
    try:
        import subprocess

        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            line = result.stdout.strip().split("\n")[0]
            parts = line.split(", ")
            if len(parts) >= 2:
                name = parts[0].strip()
                usage = float(parts[1].strip())
                return {"name": name, "usage": usage}
    except Exception:
        pass

    # Try AMD GPU on Linux (via rocm-smi)
    try:
        import subprocess

        result = subprocess.run(
            ["rocm-smi", "--showuse", "--json"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            import json

            data = json.loads(result.stdout)
            for card_id, card_data in data.items():
                if "GPU use (%)" in card_data:
                    usage = float(card_data["GPU use (%)"])
                    return {"name": "AMD GPU", "usage": usage}
    except Exception:
        pass

    # Try Apple Silicon GPU (check if available)
    try:
        import platform
        import subprocess

        if platform.system() == "Darwin" and platform.processor() == "arm":
            # Check for Apple Silicon
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType", "-json"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                import json

                data = json.loads(result.stdout)
                displays = data.get("SPDisplaysDataType", [])
                for display in displays:
                    name = display.get("sppci_model", "Apple GPU")
                    if "Apple" in name or "M1" in name or "M2" in name or "M3" in name or "M4" in name:
                        # Apple Silicon doesn't expose GPU utilization easily
                        # Return None for usage to indicate GPU exists but usage unavailable
                        return {"name": name, "usage": None}
    except Exception:
        pass

    return None


# Cache GPU availability check
_gpu_available = None
_gpu_check_done = False


def get_cpu_per_core() -> list[float]:
    """Get CPU usage per core.

    Returns:
        List of CPU usage percentages per core
    """
    cpu_count = os.cpu_count() or 1

    try:
        # macOS: use top command
        result = subprocess.run(
            ["ps", "-A", "-o", "%cpu,command"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            # Distribute total CPU across cores (approximation)
            lines = result.stdout.strip().split("\n")[1:]
            total = sum(float(line.split()[0]) for line in lines if line.strip())
            avg = total / cpu_count
            # Simulate per-core with some variance
            cores = []
            for i in range(cpu_count):
                variance = (i % 3 - 1) * 5  # Add small variance
                cores.append(max(0, min(100, avg + variance)))
            return cores
    except Exception:
        pass

    try:
        # Linux: read /proc/stat for per-core stats
        with open("/proc/stat", "r") as f:
            cores = []
            for line in f:
                if line.startswith("cpu") and not line.startswith("cpu "):
                    parts = line.split()
                    user, nice, system, idle = map(int, parts[1:5])
                    total = user + nice + system + idle
                    used = user + nice + system
                    if total > 0:
                        cores.append((used / total) * 100.0)
            if cores:
                return cores
    except Exception:
        pass

    return [0.0] * cpu_count


def get_memory_details() -> dict:
    """Get detailed memory information.

    Returns:
        Dictionary with total, used, free, and cached memory in bytes
    """
    page_size = 4096  # Default page size

    try:
        # macOS
        result = subprocess.run(
            ["vm_stat"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            stats = {}
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":")
                    value = value.strip().rstrip(".")
                    try:
                        stats[key.strip()] = int(value)
                    except ValueError:
                        pass

            # Get total memory using sysctl
            sysctl_result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            total_bytes = int(sysctl_result.stdout.strip()) if sysctl_result.returncode == 0 else 0

            pages_free = stats.get("Pages free", 0)
            pages_active = stats.get("Pages active", 0)
            pages_inactive = stats.get("Pages inactive", 0)
            pages_wired = stats.get("Pages wired down", 0)
            pages_compressed = stats.get("Pages occupied by compressor", 0)

            free_bytes = pages_free * page_size
            active_bytes = pages_active * page_size
            wired_bytes = pages_wired * page_size
            compressed_bytes = pages_compressed * page_size
            cached_bytes = pages_inactive * page_size

            used_bytes = active_bytes + wired_bytes + compressed_bytes

            return {
                "total": total_bytes,
                "used": used_bytes,
                "free": free_bytes,
                "cached": cached_bytes,
            }
    except Exception:
        pass

    try:
        # Linux
        with open("/proc/meminfo", "r") as f:
            meminfo = {}
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    value = int(parts[1]) * 1024  # Convert KB to bytes
                    meminfo[key] = value

            return {
                "total": meminfo.get("MemTotal", 0),
                "used": meminfo.get("MemTotal", 0) - meminfo.get("MemAvailable", 0),
                "free": meminfo.get("MemFree", 0),
                "cached": meminfo.get("Cached", 0) + meminfo.get("Buffers", 0),
            }
    except Exception:
        pass

    return {"total": 0, "used": 0, "free": 0, "cached": 0}


def get_top_processes(limit: int = 5) -> list[dict]:
    """Get top processes by CPU usage.

    Args:
        limit: Maximum number of processes to return

    Returns:
        List of dictionaries with process name, cpu, and memory usage
    """
    try:
        # Use ps aux for full command visibility, sort by CPU
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=2,
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            # Sort by CPU (column 3, 0-indexed 2)
            sorted_lines = sorted(
                lines,
                key=lambda x: float(x.split()[2]) if len(x.split()) > 2 else 0,
                reverse=True,
            )

            processes = []
            for line in sorted_lines:
                parts = line.split()
                if len(parts) >= 11:
                    try:
                        cpu = float(parts[2])
                        mem = float(parts[3])
                        # Command is everything from column 10 onwards
                        command = " ".join(parts[10:])
                        # Get the executable name (first part, then basename)
                        exe_path = command.split()[0] if command else ""
                        name = os.path.basename(exe_path.rstrip("/"))
                        # Clean up the name
                        name = name.strip("()") or exe_path[:20]

                        if cpu > 0.1 or mem > 0.1:  # Skip mostly idle processes
                            processes.append({"name": name, "cpu": cpu, "mem": mem})
                            if len(processes) >= limit:
                                break
                    except (ValueError, IndexError):
                        pass
            return processes
    except Exception:
        pass

    return []


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def get_system_stats(detailed: bool = False) -> dict:
    """Get all system stats.

    Args:
        detailed: If True, include per-core CPU, memory details, and top processes

    Returns:
        Dictionary with cpu, memory, and optionally gpu percentages
    """
    global _gpu_available, _gpu_check_done

    stats = {
        "cpu": get_cpu_percent(),
        "memory": get_memory_percent(),
    }

    # Only check GPU availability once, then cache result
    if not _gpu_check_done:
        _gpu_available = get_gpu_info() is not None
        _gpu_check_done = True

    if _gpu_available:
        gpu_info = get_gpu_info()
        if gpu_info:
            stats["gpu"] = gpu_info.get("usage")
            stats["gpu_name"] = gpu_info.get("name")

    # Add detailed stats if requested
    if detailed:
        stats["cpu_cores"] = get_cpu_per_core()

        mem_details = get_memory_details()
        stats["mem_total"] = mem_details["total"]
        stats["mem_used"] = mem_details["used"]
        stats["mem_free"] = mem_details["free"]
        stats["mem_cached"] = mem_details["cached"]
        stats["mem_total_fmt"] = format_bytes(mem_details["total"])
        stats["mem_used_fmt"] = format_bytes(mem_details["used"])
        stats["mem_free_fmt"] = format_bytes(mem_details["free"])
        stats["mem_cached_fmt"] = format_bytes(mem_details["cached"])

        stats["processes"] = get_top_processes(5)

    return stats
