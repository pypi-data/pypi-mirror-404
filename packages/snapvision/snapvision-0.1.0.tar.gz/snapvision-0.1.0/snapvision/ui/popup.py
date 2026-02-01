"""
Popup UI for displaying analysis results.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QHBoxLayout, QApplication, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QSize, QEvent
from PySide6.QtGui import QColor, QCursor, QFont, QIcon, QClipboard, QGuiApplication
import webbrowser
import urllib.parse
import platform


def get_system_font() -> str:
    """Get appropriate system font for the current platform."""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI"
    elif system == "Darwin":  # macOS
        return "SF Pro Display"
    else:  # Linux and others
        return "Ubuntu, DejaVu Sans, sans-serif"

class ResultPopup(QWidget):
    """
    Frameless, floating popup to display analysis results.
    """
    
    # Signals
    action_copy = Signal(str)
    action_chatgpt = Signal(str)
    closed = Signal()
    
    def __init__(self, text: str, title: str = "SnapVision", timeout: int = 0):
        super().__init__()
        
        self._text = text
        # Timeout disabled by default as per user request
        self._timeout = 0 
        self._is_closing = False
        
        self.setWindowTitle("SnapVision")
        self._setup_window()
        self._setup_ui(title, text)
        
        # Auto-close timer logic removed/disabled
            
    def _setup_window(self):
        """Configure window flags and attributes."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # Doesn't show in taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

    def _setup_ui(self, title: str, text: str):
        """Initialize the UI components."""
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Container frame (for styling and rounded corners)
        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 12px;
            }
            QLabel {
                color: #E0E0E0;
            }
            QPushButton {
                background-color: #2D2D2D;
                border: 1px solid #3E3E3E;
                border-radius: 6px;
                color: #CCCCCC;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
                border-color: #4E4E4E;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #1D1D1D;
            }
        """)
        
        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(12)
        
        # --- Header (Title + Close Button) ---
        header_layout = QHBoxLayout()
        
        # Title
        self.title_label = QLabel(title)
        title_font = QFont(get_system_font(), 10, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #00AAFF;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Close 'X' Button (Top Right)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #888;
                font-size: 14px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #331111;
                color: #FF5555;
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.close_animated)
        header_layout.addWidget(close_btn)
        
        container_layout.addLayout(header_layout)
        
        # --- Content Text ---
        # Enable Markdown and External Links
        self.content_label = QLabel(text)
        self.content_label.setWordWrap(True)
        self.content_label.setFont(QFont(get_system_font(), 10))
        self.content_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.content_label.setOpenExternalLinks(True)
        
        # Make links look good (light blue)
        # Note: Qt Style Sheets don't fully support 'line-height' directly on QLabel
        # We rely on the HTML generation from Markdown for basic spacing.
        self.content_label.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                padding: 10px;
            }
        """)
        container_layout.addWidget(self.content_label)
        
        # --- Footer Buttons Row ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Copy Button
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._handle_copy)
        button_layout.addWidget(self.copy_btn)
        
        # Chat Button
        self.chat_btn = QPushButton("Analyze with ChatGPT")
        self.chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chat_btn.clicked.connect(self._handle_chat)
        button_layout.addWidget(self.chat_btn)
        
        # Spacer
        button_layout.addStretch()
        
        # Add buttons to container
        container_layout.addLayout(button_layout)
        
        # Add container to main widget
        layout.addWidget(self.container)
        
        # Constrain width
        # Note: We use fixed width to keep the popup nice and vertical
        self.setFixedWidth(400)
    
    def show_at_cursor(self):
        """Position the popup near the cursor and show it."""
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos)
        
        if not screen:
            screen = QGuiApplication.primaryScreen()
            
        screen_geo = screen.availableGeometry()
        
        # Initial position: slightly below-right of cursor
        x = cursor_pos.x() + 20
        y = cursor_pos.y() + 20
        
        # Ensure it fits on screen
        if x + self.width() > screen_geo.right():
            x = cursor_pos.x() - self.width() - 20
        
        # We don't know height exactly until shown, but estimate
        estimated_height = self.container.sizeHint().height() + 40
        if y + estimated_height > screen_geo.bottom():
            y = cursor_pos.y() - estimated_height - 20
            
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
    
    def _handle_copy(self):
        """Copy text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self._text)
        self.copy_btn.setText("Copied! ✓")
        QTimer.singleShot(2000, lambda: self.copy_btn.setText("Copy"))
        self.action_copy.emit(self._text)
        
    def _handle_chat(self):
        """Open ChatGPT with prefilled text."""
        try:
            # Prepare prompts
            base_url = "https://chatgpt.com/"
            
            # Construct URL with query parameter
            # Note: ChatGPT uses various formats, but usually 'q' or 'prompt' query param works 
            # or simply passing it might not work depending on their A/B testing.
            # However, for now we will try the 'prompt' parameter which is common.
            # If that fails, at least copying to clipboard (which user can do) acts as fallback.
            
            encoded_text = urllib.parse.quote(self._text)
            final_url = f"{base_url}?prompt={encoded_text}"
            
            print(f"   🌐 Opening ChatGPT: {final_url}")
            webbrowser.open(final_url)
            
            # Visual feedback
            self.chat_btn.setText("Opening... ↗")
            QTimer.singleShot(2000, lambda: self.chat_btn.setText("Analyze with ChatGPT"))
            
        except Exception as e:
            print(f"   ❌ Failed to open browser: {e}")
            self.chat_btn.setText("Error ❌")
            QTimer.singleShot(2000, lambda: self.chat_btn.setText("Analyze with ChatGPT"))
            
        self.action_chatgpt.emit(self._text)
        
    def close_animated(self):
        """Close the popup (placeholder for animation)."""
        self._is_closing = True
        self.close()
        self.closed.emit()


    # --- Drag Logic ---
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() & Qt.MouseButton.LeftButton:
            if hasattr(self, '_drag_pos'):
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()

    def set_content(self, text: str, title: str = None):
        """Update the popup content dynamically."""
        self._text = text
        self.content_label.setText(text)
        if title:
            # Update title via the direct reference we saved
            if hasattr(self, 'title_label'):
                self.title_label.setText(title)
        
        # Re-calculate size based on new content
        # processEvents allows the layout to update immediately so sizeHint is accurate
        QApplication.processEvents()
        self.resize(self.sizeHint())
        self.update()
_active_popup = None

def show_result_popup(text: str, title: str = "SnapVision Analysis") -> None:
    """Show the popup with the given result."""
    global _active_popup
    
    # Close existing if open
    if _active_popup:
        try:
            _active_popup.close()
        except:
            pass
            
    _active_popup = ResultPopup(text, title)
    
    # Removed FocusOutFilter logic as per user request
    # The popup will now stay open until manually closed
    
    _active_popup.show_at_cursor()
    
    # Force UI to render immediately
    QApplication.processEvents()
        
    def _setup_ui(self, title: str, text: str):
        """Initialize the UI components."""
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Container frame (for styling and rounded corners)
        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 12px;
            }
            QLabel {
                color: #E0E0E0;
            }
            QPushButton {
                background-color: #2D2D2D;
                border: 1px solid #3E3E3E;
                border-radius: 6px;
                color: #CCCCCC;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
                border-color: #4E4E4E;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #1D1D1D;
            }
        """)
        
        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(12)
        
        # --- Header (Title + Close Button) ---
        header_layout = QHBoxLayout()
        
        # Title
        self.title_label = QLabel(title)
        title_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #00AAFF;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Close 'X' Button (Top Right)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #888;
                font-size: 14px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #331111;
                color: #FF5555;
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.close_animated)
        header_layout.addWidget(close_btn)
        
        container_layout.addLayout(header_layout)
        
        # --- Content Text ---
        # Enable Markdown and External Links
        self.content_label = QLabel(text)
        self.content_label.setWordWrap(True)
        self.content_label.setFont(QFont("Segoe UI", 10))
        self.content_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.content_label.setOpenExternalLinks(True)
        
        # Make links look good (light blue)
        # Note: Qt Style Sheets don't fully support 'line-height' directly on QLabel
        # We rely on the HTML generation from Markdown for basic spacing.
        self.content_label.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                padding: 10px;
            }
        """)
        container_layout.addWidget(self.content_label)
        
        # --- Footer Buttons Row ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Copy Button
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._handle_copy)
        button_layout.addWidget(self.copy_btn)
        
        # Chat Button
        self.chat_btn = QPushButton("Ask ChatGPT")
        self.chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chat_btn.clicked.connect(self._handle_chat)
        button_layout.addWidget(self.chat_btn)
        
        # Spacer
        button_layout.addStretch()
        
        # Add buttons to container
        container_layout.addLayout(button_layout)
        
        # Add container to main widget
        layout.addWidget(self.container)
        
        # Constrain width
        # Note: We use fixed width to keep the popup nice and vertical
        self.setFixedWidth(400)
    
    def show_at_cursor(self):
        """Position the popup near the cursor and show it."""
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos)
        
        if not screen:
            screen = QGuiApplication.primaryScreen()
            
        screen_geo = screen.availableGeometry()
        
        # Initial position: slightly below-right of cursor
        x = cursor_pos.x() + 20
        y = cursor_pos.y() + 20
        
        # Ensure it fits on screen
        if x + self.width() > screen_geo.right():
            x = cursor_pos.x() - self.width() - 20
        
        # We don't know height exactly until shown, but estimate
        estimated_height = self.container.sizeHint().height() + 40
        if y + estimated_height > screen_geo.bottom():
            y = cursor_pos.y() - estimated_height - 20
            
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
    
    def _handle_copy(self):
        """Copy text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self._text)
        self.copy_btn.setText("Copied! ✓")
        QTimer.singleShot(2000, lambda: self.copy_btn.setText("Copy"))
        self.action_copy.emit(self._text)
        
    def _handle_chat(self):
        """Emit chat signal."""
        self.action_chatgpt.emit(self._text)
        
    # Removed enterEvent and leaveEvent methods

    def close_animated(self):
        """Close the popup (placeholder for animation)."""
        self._is_closing = True
        self.close()
        self.closed.emit()


    # --- Drag Logic ---
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() & Qt.MouseButton.LeftButton:
            if hasattr(self, '_drag_pos'):
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()

    def set_content(self, text: str, title: str = None):
        """Update the popup content dynamically."""
        self._text = text
        self.content_label.setText(text)
        if title:
            # Update title via the direct reference we saved
            if hasattr(self, 'title_label'):
                self.title_label.setText(title)
        
        # Re-calculate size based on new content
        # processEvents allows the layout to update immediately so sizeHint is accurate
        QApplication.processEvents()
        self.resize(self.sizeHint())
        self.update()


# Global reference

# Global reference
_active_popup = None

def show_result_popup(text: str, title: str = "SnapVision") -> None:
    """Show the popup with the given result."""
    global _active_popup
    
    # Close existing if open
    if _active_popup:
        try:
            _active_popup.close()
        except:
            pass
            
    _active_popup = ResultPopup(text, title)
    
    # Removed FocusOutFilter logic to ensure popup stays open until manually closed
    
    _active_popup.show_at_cursor()
    
    # Force UI to render immediately
    QApplication.processEvents()

def show_processing_popup() -> None:
    """Show a 'Processing...' popup immediately."""
    show_result_popup(
        "Analyzing image...\n(This usually takes 2-4 seconds)", 
        title="Thinking..."
    )

def update_popup_text(text: str, title: str = "SnapVision") -> None:
    """Update the currently active popup text."""
    global _active_popup
    if _active_popup:
        _active_popup.set_content(text, title)
        
        # Force re-layout and resize
        _active_popup.adjustSize()
        QApplication.processEvents()
        
    else:
        # If no popup exists (rare), create one
        show_result_popup(text, title)
