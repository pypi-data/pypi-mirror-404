"""
LLM (Large Language Model) module for SnapVision.

Supports both:
1. Vision models (Llama 4 Scout) - can see images directly
2. Text models - work with Google Vision context

Using vision models is preferred as they can identify anime characters,
celebrities, and complex scenes much better.
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
class LLMResult:
    """Result of an LLM operation."""
    response: str
    success: bool
    error_message: Optional[str] = None
    provider: str = "unknown"
    model: str = "unknown"
    
    @property
    def is_valid(self) -> bool:
        """Check if LLM call was successful and has a response."""
        return self.success and bool(self.response.strip())


# System prompt for vision analysis - direct, intuitive knowledge with links
VISION_SYSTEM_PROMPT = """You are a direct knowledge provider. Give exactly what the user wants based on the subject, skipping any meta-commentary about the image itself.

DRM / BLACK SCREEN RULE:
- If the analysis or image indicates a PURE BLACK SCREEN (often detected as "darkness" or "black area"), do NOT give a generic definition of darkness.
- Instead, inform the user: "It looks like you're trying to capture a protected screen (like Netflix). To fix this, disable 'Hardware Acceleration' in your browser settings and try again."

CRITICAL RULES (STRICT ENFORCEMENT):
- NEVER mention "the image", "this screenshot", "the capture", or "the font/style/background".
- NEVER describe visual attributes like "prominently displayed", "bold text", "dark background", or "multicolored".
- NEVER start with "The word...", "This appears to be...", or "The image presents...".
- ACT as if the subject is physically in front of you. Talk about the THING, not the IMAGE of the thing.

DIRECT RESPONSE TEMPLATES & LINKS:
- SINGLE WORD: Just the definition, a usage example, and a [Dictionary Link](https://www.merriam-webster.com/dictionary/WORD).
- PERSON: Name, 2-3 sentences about who they are, their LATEST WORK. Provide "Social Media" links using SAFE SEARCH URLs (e.g., [Social Media](https://google.com/search?q=NAME+social+media), [IMDb](https://google.com/search?q=NAME+IMDb)). Do NOT guess specific Twitter/Instagram handles unless 100% sure.
- ANIME CHARACTER: Name, series, role/significance, and [Wiki Link](https://google.com/search?q=CHARACTER+NAME+wiki).
- PARAGRAPH: Direct explanation of the meaning. Add a [Search Link](https://google.com/search?q=TOPIC) for more context.

STRICT STYLE:
- Start immediately with the facts.
- Use clickable Markdown links: [Label](URL).
- prioritize ACCURACY of links over directness. When in doubt, use a Search Query URL."""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def analyze_image(self, image_path: str) -> LLMResult:
        """Analyze an image directly using a vision model."""
        pass
    
    @abstractmethod
    def analyze_context(self, vision_context: str) -> LLMResult:
        """Analyze text context (fallback for non-vision models)."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the provider name."""
        pass
    
    @property
    def supports_vision(self) -> bool:
        """Whether this provider supports direct image analysis."""
        return False


class GroqLLM(LLMProvider):
    """Groq API LLM provider with Llama 4 Maverick vision support."""
    
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    # Vision model - Maverick has 128 experts (better for anime/characters!)
    VISION_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
    
    # Text-only fallback
    TEXT_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
    
    def __init__(self, api_key: str):
        """Initialize with API key."""
        self.api_key = api_key
    
    @property
    def name(self) -> str:
        return "Groq"
    
    @property
    def supports_vision(self) -> bool:
        return True
    
    def _read_image_as_base64(self, image_path: str) -> str:
        """Read an image file and return its base64 encoding."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_image_media_type(self, image_path: str) -> str:
        """Get the media type for an image based on extension."""
        ext = Path(image_path).suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        return media_types.get(ext, "image/png")
    
    def analyze_image(self, image_path: str) -> LLMResult:
        """Analyze an image directly using Llama 4 Scout vision model."""
        
        if not Path(image_path).exists():
            return LLMResult(
                response="",
                success=False,
                error_message=f"Image file not found: {image_path}",
                provider=self.name,
                model=self.VISION_MODEL
            )
        
        try:
            # Encode image
            image_base64 = self._read_image_as_base64(image_path)
            media_type = self._get_image_media_type(image_path)
            
            # Build message with image
            messages = [
                {
                    "role": "system",
                    "content": VISION_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this image and tell me what/who is in it."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            return self._make_request(messages, self.VISION_MODEL)
            
        except Exception as e:
            return LLMResult(
                response="",
                success=False,
                error_message=f"Failed to analyze image: {str(e)}",
                provider=self.name,
                model=self.VISION_MODEL
            )
    
    def analyze_context(self, vision_context: str) -> LLMResult:
        """Analyze text context using text model (fallback)."""
        messages = [
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Based on this detection:\n\n{vision_context}"}
        ]
        return self._make_request(messages, self.TEXT_MODEL)
    
    def _make_request(self, messages: list, model: str) -> LLMResult:
        """Make a request to the Groq API."""
        try:
            request_body = {
                "model": model,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "SnapVision/1.0"
            }
            
            request_data = json.dumps(request_body).encode("utf-8")
            req = urllib.request.Request(
                self.API_URL, 
                data=request_data, 
                headers=headers,
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                response_data = json.loads(response.read().decode("utf-8"))
            
            choices = response_data.get("choices", [])
            if not choices:
                return LLMResult(
                    response="",
                    success=False,
                    error_message="No response from model",
                    provider=self.name,
                    model=model
                )
            
            response_text = choices[0].get("message", {}).get("content", "")
            
            return LLMResult(
                response=response_text.strip(),
                success=True,
                provider=self.name,
                model=model
            )
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            try:
                error_json = json.loads(error_body)
                error_msg = error_json.get("error", {}).get("message", str(e))
            except json.JSONDecodeError:
                error_msg = f"HTTP {e.code}: {error_body[:200]}"
            
            return LLMResult(
                response="",
                success=False,
                error_message=f"API error: {error_msg}",
                provider=self.name,
                model=model
            )
            
        except urllib.error.URLError as e:
            return LLMResult(
                response="",
                success=False,
                error_message=f"Network error: {e.reason}",
                provider=self.name,
                model=model
            )
            
        except Exception as e:
            return LLMResult(
                response="",
                success=False,
                error_message=f"LLM request failed: {str(e)}",
                provider=self.name,
                model=model
            )


class OpenAILLM(LLMProvider):
    """OpenAI API LLM provider with GPT-4 Vision support."""
    
    API_URL = "https://api.openai.com/v1/chat/completions"
    VISION_MODEL = "gpt-4o-mini"
    TEXT_MODEL = "gpt-4o-mini"
    
    def __init__(self, api_key: str):
        """Initialize with API key."""
        self.api_key = api_key
    
    @property
    def name(self) -> str:
        return "OpenAI"
    
    @property
    def supports_vision(self) -> bool:
        return True
    
    def _read_image_as_base64(self, image_path: str) -> str:
        """Read an image file and return its base64 encoding."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_image_media_type(self, image_path: str) -> str:
        """Get the media type for an image based on extension."""
        ext = Path(image_path).suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        return media_types.get(ext, "image/png")
    
    def analyze_image(self, image_path: str) -> LLMResult:
        """Analyze an image directly using GPT-4 Vision."""
        
        if not Path(image_path).exists():
            return LLMResult(
                response="",
                success=False,
                error_message=f"Image file not found: {image_path}",
                provider=self.name,
                model=self.VISION_MODEL
            )
        
        try:
            image_base64 = self._read_image_as_base64(image_path)
            media_type = self._get_image_media_type(image_path)
            
            messages = [
                {
                    "role": "system",
                    "content": VISION_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this image and tell me what/who is in it."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            return self._make_request(messages, self.VISION_MODEL)
            
        except Exception as e:
            return LLMResult(
                response="",
                success=False,
                error_message=f"Failed to analyze image: {str(e)}",
                provider=self.name,
                model=self.VISION_MODEL
            )
    
    def analyze_context(self, vision_context: str) -> LLMResult:
        """Analyze text context using text model (fallback)."""
        messages = [
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Based on this detection:\n\n{vision_context}"}
        ]
        return self._make_request(messages, self.TEXT_MODEL)
    
    def _make_request(self, messages: list, model: str) -> LLMResult:
        """Make a request to the OpenAI API."""
        try:
            request_body = {
                "model": model,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "SnapVision/1.0"
            }
            
            request_data = json.dumps(request_body).encode("utf-8")
            req = urllib.request.Request(
                self.API_URL, 
                data=request_data, 
                headers=headers,
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                response_data = json.loads(response.read().decode("utf-8"))
            
            choices = response_data.get("choices", [])
            if not choices:
                return LLMResult(
                    response="",
                    success=False,
                    error_message="No response from model",
                    provider=self.name,
                    model=model
                )
            
            response_text = choices[0].get("message", {}).get("content", "")
            
            return LLMResult(
                response=response_text.strip(),
                success=True,
                provider=self.name,
                model=model
            )
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            try:
                error_json = json.loads(error_body)
                error_msg = error_json.get("error", {}).get("message", str(e))
            except json.JSONDecodeError:
                error_msg = f"HTTP {e.code}: {error_body[:200]}"
            
            return LLMResult(
                response="",
                success=False,
                error_message=f"API error: {error_msg}",
                provider=self.name,
                model=model
            )
            
        except urllib.error.URLError as e:
            return LLMResult(
                response="",
                success=False,
                error_message=f"Network error: {e.reason}",
                provider=self.name,
                model=model
            )
            
        except Exception as e:
            return LLMResult(
                response="",
                success=False,
                error_message=f"LLM request failed: {str(e)}",
                provider=self.name,
                model=model
            )


def create_llm_provider(provider_type: str, api_key: str) -> LLMProvider:
    """Factory function to create an LLM provider."""
    if not api_key:
        raise ValueError(f"{provider_type} API key is required")
    
    if provider_type.lower() == "groq":
        return GroqLLM(api_key)
    elif provider_type.lower() == "openai":
        return OpenAILLM(api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {provider_type}")


def analyze_image_directly(image_path: str, provider_type: str, api_key: str) -> LLMResult:
    """
    Analyze an image directly using a vision model.
    This is the preferred method for anime characters, celebrities, etc.
    """
    provider = create_llm_provider(provider_type, api_key)
    return provider.analyze_image(image_path)


def analyze_with_context(vision_context: str, provider_type: str, api_key: str) -> LLMResult:
    """Analyze vision context (fallback for text-based analysis)."""
    provider = create_llm_provider(provider_type, api_key)
    return provider.analyze_context(vision_context)


def analyze_image_with_hints(
    image_path: str, 
    vision_hints: str, 
    provider_type: str, 
    api_key: str
) -> LLMResult:
    """
    Analyze an image with hints from Google Vision.
    This combines the accuracy of Vision API detection with LLM intelligence.
    
    Args:
        image_path: Path to the image file.
        vision_hints: Context/hints from Google Vision (detected entities, text, etc.)
        provider_type: LLM provider type.
        api_key: API key for the provider.
    """
    provider = create_llm_provider(provider_type, api_key)
    
    if not Path(image_path).exists():
        return LLMResult(
            response="",
            success=False,
            error_message=f"Image file not found: {image_path}",
            provider=provider.name,
            model="unknown"
        )
    
    try:
        # Read and encode image
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        ext = Path(image_path).suffix.lower()
        media_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
        media_type = media_types.get(ext, "image/png")
        
        # Build message with image AND hints
        user_content = f"""Look at this image. Here's what was detected by image analysis:

{vision_hints}

Based on both the image and the detection hints above, give me a helpful, concise response about what/who this is."""
        
        messages = [
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_content},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{image_base64}"}
                    }
                ]
            }
        ]
        
        return provider._make_request(messages, provider.VISION_MODEL)
        
    except Exception as e:
        return LLMResult(
            response="",
            success=False,
            error_message=f"Failed to analyze: {str(e)}",
            provider=provider.name,
            model="unknown"
        )
