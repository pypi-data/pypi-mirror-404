"""
Global hotkey listener for SnapVision.

Handles background listening for keyboard shortcuts using pynput.
Uses a thread-safe event system to communicate with the main thread.
"""

import threading
from typing import Callable, Optional
from pynput import keyboard


class HotkeyListener:
    """
    A global hotkey listener that runs in the background.
    
    This class uses pynput's GlobalHotKeys for reliable hotkey detection
    on Windows. It uses a threading.Event to signal the main thread
    when the hotkey is triggered.
    
    Attributes:
        hotkey_str: The hotkey string (e.g., "ctrl+shift+z")
    """
    
    def __init__(self, hotkey_str: str):
        """
        Initialize the hotkey listener.
        
        Args:
            hotkey_str: Hotkey combination string (e.g., "ctrl+shift+z")
        """
        self.hotkey_str = hotkey_str.lower()
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self._running = False
        self._pynput_hotkey = self._convert_to_pynput_format(hotkey_str)
        
        # Event to signal when hotkey is pressed
        self._hotkey_event = threading.Event()
    
    def _convert_to_pynput_format(self, hotkey_str: str) -> str:
        """
        Convert our hotkey format to pynput format.
        
        Our format: ctrl+shift+z
        pynput format: <ctrl>+<shift>+z
        """
        key_mapping = {
            "ctrl": "<ctrl>",
            "control": "<ctrl>",
            "shift": "<shift>",
            "alt": "<alt>",
            "cmd": "<cmd>",
            "win": "<cmd>",
        }
        
        parts = hotkey_str.lower().replace(" ", "").split("+")
        converted_parts = []
        
        for part in parts:
            if part in key_mapping:
                converted_parts.append(key_mapping[part])
            else:
                converted_parts.append(part)
        
        return "+".join(converted_parts)
    
    def _on_hotkey(self) -> None:
        """Called when the hotkey is triggered. Sets the event."""
        self._hotkey_event.set()
    
    def start(self) -> None:
        """Start the hotkey listener in the background."""
        if self._running:
            return
        
        self._running = True
        self._hotkey_event.clear()
        
        hotkeys = {
            self._pynput_hotkey: self._on_hotkey
        }
        
        self.listener = keyboard.GlobalHotKeys(hotkeys)
        self.listener.start()
    
    def stop(self) -> None:
        """Stop the hotkey listener."""
        self._running = False
        self._hotkey_event.set()  # Wake up any waiting thread
        if self.listener:
            self.listener.stop()
            self.listener = None
    
    def is_running(self) -> bool:
        """Check if the listener is currently running."""
        return self._running and self.listener is not None and self.listener.is_alive()
    
    def wait_for_hotkey(self, timeout: float = 0.1) -> bool:
        """
        Wait for the hotkey to be pressed.
        
        Args:
            timeout: Maximum time to wait in seconds.
            
        Returns:
            True if hotkey was pressed, False if timeout.
        """
        if self._hotkey_event.wait(timeout):
            self._hotkey_event.clear()
            return True
        return False


def create_hotkey_listener(hotkey: str) -> HotkeyListener:
    """
    Factory function to create a hotkey listener.
    
    Args:
        hotkey: Hotkey combination string (e.g., "ctrl+shift+z")
        
    Returns:
        Configured HotkeyListener instance
    """
    return HotkeyListener(hotkey)
