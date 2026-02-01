"""
Configuration handling for SnapVision.

Manages loading, saving, and validating configuration stored in ~/.snapvision/config.json
"""

import json
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict, field


# Default configuration directory and file
CONFIG_DIR = Path.home() / ".snapvision"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class SnapVisionConfig:
    """Configuration data class for SnapVision settings."""
    
    # OCR settings
    ocr_provider: str = "google"  # "google" or "local"
    google_vision_api_key: str = ""
    
    # LLM settings
    llm_provider: str = "groq"  # "groq" or "openai"
    llm_api_key: str = ""
    
    # Hotkey settings
    global_hotkey: str = "ctrl+shift+z"
    
    def validate(self) -> list[str]:
        """
        Validate the configuration and return a list of error messages.
        
        Returns:
            list[str]: List of validation error messages. Empty if valid.
        """
        errors = []
        
        # Validate OCR provider
        if self.ocr_provider not in ("google", "local"):
            errors.append(f"Invalid OCR provider: {self.ocr_provider}. Must be 'google' or 'local'.")
        
        # Validate Google Vision API key if using Google OCR
        if self.ocr_provider == "google" and not self.google_vision_api_key:
            errors.append("Google Vision API key is required when using Google OCR provider.")
        
        # Validate LLM provider
        if self.llm_provider not in ("groq", "openai"):
            errors.append(f"Invalid LLM provider: {self.llm_provider}. Must be 'groq' or 'openai'.")
        
        # Validate LLM API key
        if not self.llm_api_key:
            errors.append("LLM API key is required.")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "SnapVisionConfig":
        """Create configuration from dictionary."""
        return cls(
            ocr_provider=data.get("ocr_provider", "google"),
            google_vision_api_key=data.get("google_vision_api_key", ""),
            llm_provider=data.get("llm_provider", "groq"),
            llm_api_key=data.get("llm_api_key", ""),
            global_hotkey=data.get("global_hotkey", "ctrl+shift+z"),
        )


def ensure_config_dir() -> None:
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_config(config: SnapVisionConfig) -> None:
    """
    Save configuration to the config file.
    
    Args:
        config: The configuration to save.
    """
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2)


def load_config() -> Optional[SnapVisionConfig]:
    """
    Load configuration from the config file.
    
    Returns:
        SnapVisionConfig if file exists and is valid, None otherwise.
    """
    if not CONFIG_FILE.exists():
        return None
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SnapVisionConfig.from_dict(data)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load config file: {e}")
        return None


def config_exists() -> bool:
    """Check if a configuration file exists."""
    return CONFIG_FILE.exists()


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return CONFIG_FILE
