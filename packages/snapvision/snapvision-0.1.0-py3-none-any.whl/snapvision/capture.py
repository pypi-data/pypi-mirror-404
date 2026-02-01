"""
Screen capture functionality for SnapVision.

Handles capturing screen regions and saving them as images.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

import mss
import mss.tools


@dataclass
class CaptureResult:
    """Result of a screen capture operation."""
    image_path: str
    width: int
    height: int
    success: bool
    error_message: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if capture was successful."""
        return self.success and os.path.exists(self.image_path)


def get_capture_directory() -> Path:
    """
    Get the directory for storing captured images.
    
    Creates the directory if it doesn't exist.
    
    Returns:
        Path to the capture directory.
    """
    capture_dir = Path.home() / ".snapvision" / "captures"
    capture_dir.mkdir(parents=True, exist_ok=True)
    return capture_dir


def generate_capture_filename() -> str:
    """
    Generate a unique filename for a capture.
    
    Returns:
        Filename with timestamp (e.g., 'capture_20240131_143052.png')
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"capture_{timestamp}.png"


def capture_region(
    x: int,
    y: int,
    width: int,
    height: int,
    save_path: Optional[str] = None
) -> CaptureResult:
    """
    Capture a specific region of the screen.
    
    Args:
        x: Left coordinate of the region.
        y: Top coordinate of the region.
        width: Width of the region in pixels.
        height: Height of the region in pixels.
        save_path: Optional path to save the image. If not provided,
                   saves to the default capture directory.
    
    Returns:
        CaptureResult with the path to the saved image.
    """
    # Validate dimensions
    if width <= 0 or height <= 0:
        return CaptureResult(
            image_path="",
            width=0,
            height=0,
            success=False,
            error_message="Invalid region dimensions (width and height must be positive)"
        )
    
    # Determine save path
    if save_path is None:
        capture_dir = get_capture_directory()
        filename = generate_capture_filename()
        save_path = str(capture_dir / filename)
    
    try:
        # Define the region to capture
        # mss uses a dict with 'left', 'top', 'width', 'height'
        monitor = {
            "left": x,
            "top": y,
            "width": width,
            "height": height,
        }
        
        # Capture the screen region
        with mss.mss() as sct:
            screenshot = sct.grab(monitor)
            
            # Save as PNG
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=save_path)
        
        return CaptureResult(
            image_path=save_path,
            width=width,
            height=height,
            success=True
        )
        
    except Exception as e:
        return CaptureResult(
            image_path="",
            width=0,
            height=0,
            success=False,
            error_message=f"Failed to capture screen: {str(e)}"
        )


def capture_full_screen(monitor_index: int = 0, save_path: Optional[str] = None) -> CaptureResult:
    """
    Capture a full screen/monitor.
    
    Args:
        monitor_index: Index of the monitor to capture (0 = all monitors, 1+ = specific monitor).
        save_path: Optional path to save the image.
    
    Returns:
        CaptureResult with the path to the saved image.
    """
    if save_path is None:
        capture_dir = get_capture_directory()
        filename = generate_capture_filename()
        save_path = str(capture_dir / filename)
    
    try:
        with mss.mss() as sct:
            # sct.monitors[0] is all monitors combined
            # sct.monitors[1+] are individual monitors
            if monitor_index >= len(sct.monitors):
                monitor_index = 0
            
            monitor = sct.monitors[monitor_index]
            screenshot = sct.grab(monitor)
            
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=save_path)
            
            return CaptureResult(
                image_path=save_path,
                width=monitor["width"],
                height=monitor["height"],
                success=True
            )
            
    except Exception as e:
        return CaptureResult(
            image_path="",
            width=0,
            height=0,
            success=False,
            error_message=f"Failed to capture screen: {str(e)}"
        )


def cleanup_old_captures(max_age_hours: int = 24) -> int:
    """
    Remove capture files older than the specified age.
    
    Args:
        max_age_hours: Maximum age in hours. Files older than this will be deleted.
    
    Returns:
        Number of files deleted.
    """
    capture_dir = get_capture_directory()
    deleted_count = 0
    
    if not capture_dir.exists():
        return 0
    
    now = datetime.now()
    
    for file_path in capture_dir.glob("capture_*.png"):
        try:
            # Get file modification time
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_hours = (now - mtime).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                file_path.unlink()
                deleted_count += 1
                
        except Exception:
            # Skip files that can't be processed
            pass
    
    return deleted_count
