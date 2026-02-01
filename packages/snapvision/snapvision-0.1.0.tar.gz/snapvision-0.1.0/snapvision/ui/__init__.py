"""
Screen region selection overlay for SnapVision.

Provides a fullscreen transparent overlay that allows users to
drag-select a rectangular region of the screen.
"""

import sys
import ctypes
from dataclasses import dataclass
from typing import Optional, Tuple
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QPoint, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QScreen, QGuiApplication, QPixmap


@dataclass
class SelectionResult:
    """Result of a screen region selection."""
    x: int
    y: int
    width: int
    height: int
    cancelled: bool = False
    captured_path: Optional[str] = None
    
    @property
    def region(self) -> Tuple[int, int, int, int]:
        """Return region as (x, y, width, height) tuple."""
        return (self.x, self.y, self.width, self.height)
    
    @property
    def is_valid(self) -> bool:
        """Check if selection is valid (non-zero size and not cancelled)."""
        return not self.cancelled and self.width > 0 and self.height > 0


class SelectionOverlay(QWidget):
    """
    Fullscreen transparent overlay for drag-selecting a screen region.
    
    The overlay covers the entire screen with a semi-transparent dark layer.
    Users can click and drag to select a rectangular region. The selected
    region is shown as a clear window through the dark overlay.
    
    Signals:
        selection_complete: Emitted when selection is done, with SelectionResult
    """
    
    selection_complete = Signal(object)
    
    def __init__(self, background: Optional[QPixmap] = None):
        """
        Initialize the selection overlay.
        
        Args:
            background: Optional full-screen screenshot to show as background.
        """
        super().__init__()
        
        # Selection state
        self._background = background
        self._start_point: Optional[QPoint] = None
        self._current_point: Optional[QPoint] = None
        self._is_selecting = False
        self._result: Optional[SelectionResult] = None
        
        # Configure window
        self._setup_window()
    
    def _setup_window(self) -> None:
        """Configure the overlay window properties."""
        # Frameless, always-on-top, tool window (no taskbar)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Cover all screens (multi-monitor support)
        geometry = self._get_combined_screen_geometry()
        self.setGeometry(geometry)
        
        # Set cursor to crosshair
        self.setCursor(Qt.CursorShape.CrossCursor)
    
    def _get_combined_screen_geometry(self) -> QRect:
        """Get the combined geometry of all screens."""
        screens = QGuiApplication.screens()
        if not screens:
            # Fallback to primary screen
            primary = QGuiApplication.primaryScreen()
            return primary.geometry() if primary else QRect(0, 0, 1920, 1080)
        
        # Combine all screen geometries
        combined = screens[0].geometry()
        for screen in screens[1:]:
            combined = combined.united(screen.geometry())
        
        return combined
    
    def paintEvent(self, event) -> None:
        """
        Paint the overlay with semi-transparent background and selection rectangle.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw frozen background if available
        if self._background:
            painter.drawPixmap(self.rect(), self._background)
        
        # Semi-transparent dark overlay
        overlay_color = QColor(0, 0, 0, 150)  # Dark overlay
        painter.fillRect(self.rect(), overlay_color)
        
        # Draw selection rectangle if selecting
        if self._start_point and self._current_point:
            selection_rect = self._get_selection_rect()
            
            # If we have a background, draw the corresponding piece of it 
            # without the dark overlay on top.
            # If we have a background, draw the corresponding piece of it 
            # without the dark overlay on top.
            if self._background:
                # RATIO-BASED DRAWING
                # We must scale the logical selection rect to the physical image coordinates
                # to find the correct source rectangle to draw.
                img_w = self._background.width()
                img_h = self._background.height()
                screen_w = self.width()
                screen_h = self.height()
                
                if screen_w > 0 and screen_h > 0:
                    scale_x = img_w / screen_w
                    scale_y = img_h / screen_h
                    
                    source_rect = QRect(
                        int(selection_rect.x() * scale_x),
                        int(selection_rect.y() * scale_y),
                        int(selection_rect.width() * scale_x),
                        int(selection_rect.height() * scale_y)
                    )
                    painter.drawPixmap(selection_rect, self._background, source_rect)
                else:
                    painter.drawPixmap(selection_rect, self._background, selection_rect)
            else:
                # Fallback: clear the area (transparent)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                painter.fillRect(selection_rect, Qt.GlobalColor.transparent)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            # Draw selection border
            border_pen = QPen(QColor(0, 150, 255), 2)  # Blue border
            painter.setPen(border_pen)
            painter.drawRect(selection_rect)
            
            # Draw corner handles
            handle_size = 8
            handle_color = QColor(0, 150, 255)
            painter.setBrush(handle_color)
            painter.setPen(Qt.PenStyle.NoPen)
            
            corners = [
                selection_rect.topLeft(),
                selection_rect.topRight(),
                selection_rect.bottomLeft(),
                selection_rect.bottomRight(),
            ]
            for corner in corners:
                handle_rect = QRect(
                    corner.x() - handle_size // 2,
                    corner.y() - handle_size // 2,
                    handle_size,
                    handle_size
                )
                painter.drawRect(handle_rect)
            
            # Draw dimensions text
            self._draw_dimensions(painter, selection_rect)
        
        # Draw instructions
        self._draw_instructions(painter)
    
    def _draw_dimensions(self, painter: QPainter, rect: QRect) -> None:
        """Draw the width x height dimensions near the selection."""
        dimensions_text = f"{rect.width()} × {rect.height()}"
        
        # Position text below the selection
        text_x = rect.center().x() - 40
        text_y = rect.bottom() + 25
        
        # Background for text
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 180))
        text_rect = QRect(text_x - 5, text_y - 15, 90, 22)
        painter.drawRoundedRect(text_rect, 4, 4)
        
        # Draw text
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(text_x, text_y, dimensions_text)
    
    def _draw_instructions(self, painter: QPainter) -> None:
        """Draw usage instructions at the top of the screen."""
        instruction_text = "Click and drag to select a region  •  Press ESC to cancel"
        
        # Position at top center
        screen_width = self.width()
        text_x = screen_width // 2 - 200
        text_y = 50
        
        # Background for instructions
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 180))
        text_rect = QRect(text_x - 10, text_y - 20, 420, 30)
        painter.drawRoundedRect(text_rect, 6, 6)
        
        # Draw text
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(text_x, text_y, instruction_text)
    
    def _get_selection_rect(self) -> QRect:
        """Calculate the normalized selection rectangle."""
        if not self._start_point or not self._current_point:
            return QRect()
        
        # Normalize to handle any drag direction
        x1, y1 = self._start_point.x(), self._start_point.y()
        x2, y2 = self._current_point.x(), self._current_point.y()
        
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        return QRect(left, top, width, height)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press to start selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_point = event.pos()
            self._current_point = event.pos()
            self._is_selecting = True
            self.update()
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move to update selection rectangle."""
        if self._is_selecting:
            self._current_point = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release to complete selection."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._current_point = event.pos()
            self._is_selecting = False
            
            # Local rect (logical coordinates on the overlay widget)
            rect = self._get_selection_rect()
            
            # Global coordinates (for fallback/reference)
            global_top_left = self.mapToGlobal(rect.topLeft())
            
            # Create result
            self._result = SelectionResult(
                x=global_top_left.x(),
                y=global_top_left.y(),
                width=rect.width(),
                height=rect.height(),
                cancelled=False
            )
            
            # Save the cropped region from the frozen background
            # RATIO-BASED CROP (DPI Agnostic)
            if self._background and not rect.isEmpty():
                try:
                    from snapvision.capture import get_capture_directory, generate_capture_filename
                    save_path = str(get_capture_directory() / generate_capture_filename())
                    
                    # 1. Get physical dimensions of the background image
                    img_w = self._background.width()
                    img_h = self._background.height()
                    
                    # 2. Get logical dimensions of the widget (screen)
                    screen_w = self.width()
                    screen_h = self.height()
                    
                    # 3. Calculate Scale Factor (Physical / Logical)
                    if screen_w > 0 and screen_h > 0:
                        scale_x = img_w / screen_w
                        scale_y = img_h / screen_h
                        
                        # 4. Map Selection Rect to Image Coordinates
                        crop_x = int(rect.x() * scale_x)
                        crop_y = int(rect.y() * scale_y)
                        crop_w = int(rect.width() * scale_x)
                        crop_h = int(rect.height() * scale_y)
                        
                        # 5. Crop
                        cropped = self._background.copy(crop_x, crop_y, crop_w, crop_h)
                        if cropped.save(save_path, "PNG"):
                            self._result.captured_path = save_path
                            print(f"   ❄️  Frozen Capture Saved: {crop_w}x{crop_h} at ({crop_x},{crop_y})")
                            
                except Exception as e:
                    print(f"   ⚠️  Failed to save frozen capture: {e}")
            
            # Close overlay and emit result
            self.close()
            self.selection_complete.emit(self._result)


def select_screen_region() -> Optional[SelectionResult]:
    """
    Show the selection overlay and return the selected region.
    """
    from PySide6.QtCore import QEventLoop
    
    # Check if QApplication exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Take a FULL DESKTOP screenshot to "freeze" the view using MSS
    # This captures the raw physical pixels of that setup.
    screenshot = None
    import mss
    import numpy as np
    from PySide6.QtGui import QImage, QPixmap
    
    try:
        with mss.mss() as sct:
            # Monitor 0 is the "All in One" composite of all screens
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            
            # Convert to QPixmap
            img = QImage(sct_img.bgra, sct_img.width, sct_img.height, QImage.Format.Format_ARGB32)
            screenshot = QPixmap.fromImage(img)
            
            # IMPORTANT: We do NOT set DevicePixelRatio here.
            # We want the painter to treat this as a raw 1:1 bitmap and stretch it 
            # to fit the overlay window. This creates the "Map" we need for accurate cropping.
            
    except Exception as e:
        print(f"   ⚠️  Failed to take frozen screenshot: {e}")
        # Fallback to simple grab
        screens = QGuiApplication.screens()
        if screens:
            screenshot = screens[0].grabWindow(0)
    
    # Create and show overlay
    overlay = SelectionOverlay(background=screenshot)
    result_container = [None]
    
    loop = QEventLoop()
    def on_selection_complete(result):
        result_container[0] = result
        loop.quit()
    
    overlay.selection_complete.connect(on_selection_complete)
    overlay.showFullScreen()
    
    loop.exec()
    overlay.deleteLater()
    
    return result_container[0]
