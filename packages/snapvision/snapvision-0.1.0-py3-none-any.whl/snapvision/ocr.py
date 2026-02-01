"""
OCR (Optical Character Recognition) module for SnapVision.

Provides an abstraction layer for OCR functionality with support for
multiple providers (Google Vision, local fallback).
"""

import base64
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error


@dataclass
class OCRResult:
    """Result of an OCR operation."""
    text: str
    success: bool
    error_message: Optional[str] = None
    provider: str = "unknown"
    
    @property
    def is_valid(self) -> bool:
        """Check if OCR was successful and has text."""
        return self.success and bool(self.text.strip())
    
    @property
    def cleaned_text(self) -> str:
        """Get cleaned text with normalized whitespace."""
        if not self.text:
            return ""
        # Normalize whitespace but preserve paragraph structure
        lines = self.text.split('\n')
        cleaned_lines = [' '.join(line.split()) for line in lines]
        return '\n'.join(line for line in cleaned_lines if line)


class OCRProvider(ABC):
    """Abstract base class for OCR providers."""
    
    @abstractmethod
    def extract_text(self, image_path: str) -> OCRResult:
        """
        Extract text from an image.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            OCRResult with extracted text or error information.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the provider name."""
        pass


class GoogleVisionOCR(OCRProvider):
    """
    Google Cloud Vision API OCR provider.
    
    Uses the REST API directly without requiring the google-cloud-vision
    library, making it lighter weight.
    """
    
    API_URL = "https://vision.googleapis.com/v1/images:annotate"
    
    def __init__(self, api_key: str):
        """
        Initialize the Google Vision OCR provider.
        
        Args:
            api_key: Google Cloud Vision API key.
        """
        self.api_key = api_key
    
    @property
    def name(self) -> str:
        return "Google Vision"
    
    def _read_image_as_base64(self, image_path: str) -> str:
        """Read an image file and return its base64 encoding."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def extract_text(self, image_path: str) -> OCRResult:
        """
        Extract text from an image using Google Cloud Vision API.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            OCRResult with extracted text or error information.
        """
        # Validate image exists
        if not Path(image_path).exists():
            return OCRResult(
                text="",
                success=False,
                error_message=f"Image file not found: {image_path}",
                provider=self.name
            )
        
        try:
            # Read and encode image
            image_base64 = self._read_image_as_base64(image_path)
            
            # Prepare API request
            request_body = {
                "requests": [
                    {
                        "image": {
                            "content": image_base64
                        },
                        "features": [
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 1
                            }
                        ]
                    }
                ]
            }
            
            # Make API request
            url = f"{self.API_URL}?key={self.api_key}"
            headers = {
                "Content-Type": "application/json"
            }
            
            request_data = json.dumps(request_body).encode("utf-8")
            req = urllib.request.Request(url, data=request_data, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode("utf-8"))
            
            # Parse response
            return self._parse_response(response_data)
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            try:
                error_json = json.loads(error_body)
                error_msg = error_json.get("error", {}).get("message", str(e))
            except json.JSONDecodeError:
                error_msg = str(e)
            
            return OCRResult(
                text="",
                success=False,
                error_message=f"API error: {error_msg}",
                provider=self.name
            )
            
        except urllib.error.URLError as e:
            return OCRResult(
                text="",
                success=False,
                error_message=f"Network error: {e.reason}",
                provider=self.name
            )
            
        except Exception as e:
            return OCRResult(
                text="",
                success=False,
                error_message=f"OCR failed: {str(e)}",
                provider=self.name
            )
    
    def _parse_response(self, response_data: dict) -> OCRResult:
        """Parse the Google Vision API response."""
        try:
            responses = response_data.get("responses", [])
            
            if not responses:
                return OCRResult(
                    text="",
                    success=True,
                    error_message="No text detected in image",
                    provider=self.name
                )
            
            first_response = responses[0]
            
            # Check for errors in response
            if "error" in first_response:
                error = first_response["error"]
                return OCRResult(
                    text="",
                    success=False,
                    error_message=f"API error: {error.get('message', 'Unknown error')}",
                    provider=self.name
                )
            
            # Get full text annotation
            text_annotations = first_response.get("textAnnotations", [])
            
            if not text_annotations:
                return OCRResult(
                    text="",
                    success=True,
                    error_message="No text detected in image",
                    provider=self.name
                )
            
            # First annotation contains the full text
            full_text = text_annotations[0].get("description", "")
            
            return OCRResult(
                text=full_text.strip(),
                success=True,
                provider=self.name
            )
            
        except Exception as e:
            return OCRResult(
                text="",
                success=False,
                error_message=f"Failed to parse response: {str(e)}",
                provider=self.name
            )


class LocalOCR(OCRProvider):
    """
    Local OCR provider placeholder.
    
    This is a placeholder for future local OCR implementation
    (e.g., using Tesseract or other local libraries).
    """
    
    @property
    def name(self) -> str:
        return "Local OCR"
    
    def extract_text(self, image_path: str) -> OCRResult:
        """
        Extract text using local OCR (not yet implemented).
        
        Returns:
            OCRResult indicating local OCR is not available.
        """
        return OCRResult(
            text="",
            success=False,
            error_message="Local OCR is not yet implemented. Please use Google Vision.",
            provider=self.name
        )


def create_ocr_provider(provider_type: str, api_key: str = "") -> OCRProvider:
    """
    Factory function to create an OCR provider.
    
    Args:
        provider_type: Type of provider ("google" or "local").
        api_key: API key (required for Google Vision).
        
    Returns:
        Configured OCR provider instance.
    """
    if provider_type.lower() == "google":
        if not api_key:
            raise ValueError("Google Vision API key is required")
        return GoogleVisionOCR(api_key)
    elif provider_type.lower() == "local":
        return LocalOCR()
    else:
        raise ValueError(f"Unknown OCR provider: {provider_type}")


def extract_text(image_path: str, provider_type: str = "google", api_key: str = "") -> OCRResult:
    """
    Convenience function to extract text from an image.
    
    Args:
        image_path: Path to the image file.
        provider_type: Type of OCR provider to use.
        api_key: API key for the provider.
        
    Returns:
        OCRResult with extracted text or error information.
    """
    provider = create_ocr_provider(provider_type, api_key)
    return provider.extract_text(image_path)
