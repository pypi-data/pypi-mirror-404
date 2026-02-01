"""
Vision analysis module for SnapVision.

Uses Google Vision API to detect all visual elements in an image:
- Text (OCR)
- Objects and Labels
- Faces
- Landmarks
- Colors
- Web entities

This context is then passed to an LLM for detailed analysis.
"""

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict
import urllib.request
import urllib.error


@dataclass
class VisionAnalysis:
    """Complete visual analysis of an image from Google Vision."""
    
    # Text detection
    text: str = ""
    
    # Label detection (what's in the image)
    labels: List[str] = field(default_factory=list)
    
    # Object detection with locations
    objects: List[str] = field(default_factory=list)
    
    # Face detection info
    faces: List[Dict] = field(default_factory=list)
    
    # Landmark detection
    landmarks: List[str] = field(default_factory=list)
    
    # Web entities (celebrities, famous things, topics)
    web_entities: List[str] = field(default_factory=list)
    
    # Best guess labels (what Google thinks this image is)
    best_guess: List[str] = field(default_factory=list)
    
    # Matching pages (where this image appears on the web)
    matching_pages: List[str] = field(default_factory=list)
    
    # Dominant colors
    colors: List[str] = field(default_factory=list)
    
    # Status
    success: bool = False
    error_message: Optional[str] = None
    
    def to_context(self) -> str:
        """Convert analysis to a text context for the LLM."""
        parts = []
        
        # Best guess is often the most useful - contains celebrity names, etc.
        if self.best_guess:
            parts.append(f"**Identified as:** {', '.join(self.best_guess)}")
        
        # Web entities often contain person names, celebrities, brands
        if self.web_entities:
            parts.append(f"**Recognized entities (people, brands, topics):** {', '.join(self.web_entities[:8])}")
        
        if self.text:
            parts.append(f"**Text detected in image:**\n{self.text}")
        
        if self.labels:
            parts.append(f"**Labels/Categories:** {', '.join(self.labels)}")
        
        if self.objects:
            parts.append(f"**Objects detected:** {', '.join(self.objects)}")
        
        if self.faces:
            face_descriptions = []
            for i, face in enumerate(self.faces, 1):
                emotions = []
                if face.get("joy"):
                    emotions.append("joyful")
                if face.get("sorrow"):
                    emotions.append("sad")
                if face.get("anger"):
                    emotions.append("angry")
                if face.get("surprise"):
                    emotions.append("surprised")
                
                if emotions:
                    face_descriptions.append(f"Face {i}: appears {', '.join(emotions)}")
                else:
                    face_descriptions.append(f"Face {i}: neutral expression")
            
            parts.append(f"**Faces detected ({len(self.faces)}):** {'; '.join(face_descriptions)}")
        
        if self.landmarks:
            parts.append(f"**Landmarks:** {', '.join(self.landmarks)}")
        
        if self.matching_pages:
            parts.append(f"**Image found on web pages about:** {', '.join(self.matching_pages[:3])}")
        
        if self.colors:
            parts.append(f"**Dominant colors:** {', '.join(self.colors[:3])}")
        
        if not parts:
            return "No visual elements detected in the image."
        
        return "\n\n".join(parts)
    
    @property
    def has_content(self) -> bool:
        """Check if any content was detected."""
        return bool(
            self.text or self.labels or self.objects or 
            self.faces or self.landmarks or self.web_entities or
            self.best_guess
        )


class GoogleVisionAnalyzer:
    """
    Google Cloud Vision API analyzer.
    
    Detects multiple features in an image using a single API call.
    """
    
    API_URL = "https://vision.googleapis.com/v1/images:annotate"
    
    def __init__(self, api_key: str):
        """Initialize with API key."""
        self.api_key = api_key
    
    def _read_image_as_base64(self, image_path: str) -> str:
        """Read an image file and return its base64 encoding."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def analyze(self, image_path: str) -> VisionAnalysis:
        """
        Analyze an image using Google Vision API.
        
        Detects text, labels, objects, faces, landmarks, and more.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            VisionAnalysis with all detected elements.
        """
        # Validate image exists
        if not Path(image_path).exists():
            return VisionAnalysis(
                success=False,
                error_message=f"Image file not found: {image_path}"
            )
        
        try:
            # Read and encode image
            image_base64 = self._read_image_as_base64(image_path)
            
            # Request all feature types
            request_body = {
                "requests": [
                    {
                        "image": {
                            "content": image_base64
                        },
                        "features": [
                            {"type": "TEXT_DETECTION", "maxResults": 1},
                            {"type": "LABEL_DETECTION", "maxResults": 10},
                            {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                            {"type": "FACE_DETECTION", "maxResults": 5},
                            {"type": "LANDMARK_DETECTION", "maxResults": 5},
                            {"type": "WEB_DETECTION", "maxResults": 5},
                            {"type": "IMAGE_PROPERTIES"}
                        ]
                    }
                ]
            }
            
            # Make API request
            url = f"{self.API_URL}?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            
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
            
            return VisionAnalysis(
                success=False,
                error_message=f"API error: {error_msg}"
            )
            
        except urllib.error.URLError as e:
            return VisionAnalysis(
                success=False,
                error_message=f"Network error: {e.reason}"
            )
            
        except Exception as e:
            return VisionAnalysis(
                success=False,
                error_message=f"Analysis failed: {str(e)}"
            )
    
    def _parse_response(self, response_data: dict) -> VisionAnalysis:
        """Parse the Google Vision API response."""
        try:
            responses = response_data.get("responses", [])
            
            if not responses:
                return VisionAnalysis(
                    success=True,
                    error_message="No content detected in image"
                )
            
            first_response = responses[0]
            
            # Check for errors
            if "error" in first_response:
                error = first_response["error"]
                return VisionAnalysis(
                    success=False,
                    error_message=f"API error: {error.get('message', 'Unknown error')}"
                )
            
            analysis = VisionAnalysis(success=True)
            
            # Extract text
            text_annotations = first_response.get("textAnnotations", [])
            if text_annotations:
                analysis.text = text_annotations[0].get("description", "").strip()
            
            # Extract labels
            label_annotations = first_response.get("labelAnnotations", [])
            analysis.labels = [
                label.get("description", "")
                for label in label_annotations
                if label.get("score", 0) > 0.5
            ]
            
            # Extract objects
            object_annotations = first_response.get("localizedObjectAnnotations", [])
            analysis.objects = [
                obj.get("name", "")
                for obj in object_annotations
                if obj.get("score", 0) > 0.5
            ]
            
            # Extract faces
            face_annotations = first_response.get("faceAnnotations", [])
            for face in face_annotations:
                face_info = {
                    "joy": self._likelihood_to_bool(face.get("joyLikelihood")),
                    "sorrow": self._likelihood_to_bool(face.get("sorrowLikelihood")),
                    "anger": self._likelihood_to_bool(face.get("angerLikelihood")),
                    "surprise": self._likelihood_to_bool(face.get("surpriseLikelihood")),
                }
                analysis.faces.append(face_info)
            
            # Extract landmarks
            landmark_annotations = first_response.get("landmarkAnnotations", [])
            analysis.landmarks = [
                lm.get("description", "")
                for lm in landmark_annotations
            ]
            
            # Extract web detection (celebrities, brands, etc.)
            web_detection = first_response.get("webDetection", {})
            
            # Web entities - often contains celebrity names, brands, topics
            web_entities = web_detection.get("webEntities", [])
            analysis.web_entities = [
                entity.get("description", "")
                for entity in web_entities
                if entity.get("description") and entity.get("score", 0) > 0.3
            ]
            
            # Best guess labels - Google's best guess for what the image is
            # This often contains celebrity names!
            best_guess_labels = web_detection.get("bestGuessLabels", [])
            analysis.best_guess = [
                label.get("label", "")
                for label in best_guess_labels
                if label.get("label")
            ]
            
            # Pages with matching images - titles often contain person names
            pages_with_matching = web_detection.get("pagesWithMatchingImages", [])
            for page in pages_with_matching[:3]:
                title = page.get("pageTitle", "")
                if title:
                    # Clean up the title
                    title = title.split(" - ")[0].split(" | ")[0].strip()
                    if title and len(title) < 100:
                        analysis.matching_pages.append(title)
            
            # Extract dominant colors
            image_props = first_response.get("imagePropertiesAnnotation", {})
            dominant_colors = image_props.get("dominantColors", {}).get("colors", [])
            for color_info in dominant_colors[:3]:
                color = color_info.get("color", {})
                r, g, b = int(color.get("red", 0)), int(color.get("green", 0)), int(color.get("blue", 0))
                color_name = self._rgb_to_name(r, g, b)
                if color_name:
                    analysis.colors.append(color_name)
            
            return analysis
            
        except Exception as e:
            return VisionAnalysis(
                success=False,
                error_message=f"Failed to parse response: {str(e)}"
            )
    
    def _likelihood_to_bool(self, likelihood: str) -> bool:
        """Convert Google's likelihood string to boolean."""
        return likelihood in ("LIKELY", "VERY_LIKELY")
    
    def _rgb_to_name(self, r: int, g: int, b: int) -> str:
        """Convert RGB values to approximate color name."""
        # Simple color naming
        if r > 200 and g > 200 and b > 200:
            return "white"
        if r < 50 and g < 50 and b < 50:
            return "black"
        if r > 200 and g < 100 and b < 100:
            return "red"
        if r < 100 and g > 200 and b < 100:
            return "green"
        if r < 100 and g < 100 and b > 200:
            return "blue"
        if r > 200 and g > 200 and b < 100:
            return "yellow"
        if r > 200 and g < 100 and b > 200:
            return "magenta"
        if r < 100 and g > 200 and b > 200:
            return "cyan"
        if r > 150 and g > 100 and b < 100:
            return "orange"
        if r > 100 and g > 100 and b > 100:
            return "gray"
        return ""


def analyze_image(image_path: str, api_key: str) -> VisionAnalysis:
    """
    Convenience function to analyze an image.
    
    Args:
        image_path: Path to the image file.
        api_key: Google Vision API key.
        
    Returns:
        VisionAnalysis with all detected elements.
    """
    analyzer = GoogleVisionAnalyzer(api_key)
    return analyzer.analyze(image_path)
