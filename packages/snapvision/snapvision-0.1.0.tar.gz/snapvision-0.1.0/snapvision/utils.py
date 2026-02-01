"""
Utility functions for SnapVision.

Contains shared helper functions used across the application.
"""

from pathlib import Path
from typing import Optional


def get_temp_dir() -> Path:
    """
    Get the temporary directory for SnapVision files.
    
    Returns:
        Path to the temporary directory.
    """
    temp_dir = Path.home() / ".snapvision" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def mask_api_key(key: str, visible_chars: int = 4) -> str:
    """
    Mask an API key for display, showing only the last few characters.
    
    Args:
        key: The API key to mask.
        visible_chars: Number of characters to show at the end.
    
    Returns:
        Masked API key string.
    """
    if not key:
        return "(not set)"
    
    if len(key) <= visible_chars:
        return "*" * len(key)
    
    return "*" * masked_length + key[-visible_chars:]


# --- Process Management ---

def get_pid_file() -> Path:
    """Get path to the PID file."""
    pid_file = Path.home() / ".snapvision" / "snapvision.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    return pid_file


def write_pid() -> None:
    """Write current process ID to lock file."""
    import os
    pid = os.getpid()
    pid_file = get_pid_file()
    try:
        pid_file.write_text(str(pid))
    except Exception:
        pass


def read_pid() -> Optional[int]:
    """Read PID from lock file."""
    pid_file = get_pid_file()
    if not pid_file.exists():
        return None
    try:
        return int(pid_file.read_text().strip())
    except (ValueError, OSError):
        return None


def remove_pid_file() -> None:
    """Remove the PID file."""
    pid_file = get_pid_file()
    try:
        if pid_file.exists():
            pid_file.unlink()
    except Exception:
        pass


def is_process_running(pid: int) -> bool:
    """Check if a process with the given PID is running."""
    import platform
    
    if pid is None:
        return False
        
    try:
        if platform.system() == "Windows":
            import ctypes
            
            # Windows API constants
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            
            kernel32 = ctypes.windll.kernel32
            
            # Try to open the process
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            
            if handle == 0:
                # Could not open process - it doesn't exist or no access
                return False
                
            try:
                # Check if the process is still active
                exit_code = ctypes.c_ulong()
                if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    return exit_code.value == STILL_ACTIVE
                return False
            finally:
                kernel32.CloseHandle(handle)
        else:
            # Unix - os.kill with signal 0 just checks if process exists
            import os
            os.kill(pid, 0)
            return True
            
    except (OSError, Exception):
        return False
