import os
import sys
from PyQt6.QtWidgets import (
    QLabel, QPushButton, QLineEdit, QComboBox, QWidget,
    QCheckBox, QProgressBar, QScrollBar, QSlider, 
    QVBoxLayout, QHBoxLayout, QTabWidget, QGraphicsBlurEffect,
    QGraphicsOpacityEffect, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QToolBar, QSystemTrayIcon, QMenu,
    QApplication, QScroller, QGestureEvent, QPinchGesture, QPanGesture
)
from PyQt6.QtGui import QAction, QIcon, QCursor, QPalette, QColor, QPainter, QBrush
from PyQt6.QtCore import QUrl, Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, QRect, QEvent

# --- v1.0.0 Touch & Mobile Optimization ---

class TouchScrollArea:
    """A container that enables mobile-style kinetic scrolling (swipe to scroll)."""
    def __init__(self, widget):
        self.qt_widget = widget
        # Enable kinetic scrolling (flick) - Essential for Android/Touch feel
        QScroller.grabGesture(self.qt_widget, QScroller.ScrollerGestureType.LeftMouseButtonGesture)
        
        # Optimize scrollbar for touch (hide or make thin for modern aesthetic)
        if hasattr(self.qt_widget, 'verticalScrollBar'):
            self.qt_widget.verticalScrollBar().setStyleSheet("width: 5px; background: transparent;")

class TouchButton(QPushButton):
    """A button optimized for fingers: larger hit area and press feedback."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.qt_widget = self
        self.setMinimumHeight(50) # Minimum finger-friendly height (Android standard)
        self.setStyleSheet("""
            QPushButton { 
                background-color: #007AFF; color: white; border-radius: 10px; 
                font-size: 14pt; padding: 10px; border: none;
            }
            QPushButton:pressed { background-color: #0051A8; }
        """)

    def mousePressEvent(self, event):
        # Visual feedback for touch
        self.setGraphicsEffect(QGraphicsOpacityEffect(opacity=0.7))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setGraphicsEffect(None)
        super().mouseReleaseEvent(event)

class GestureWidget(QWidget):
    """A base widget that detects Pinches and Pans (Swipes) for tablets."""
    def __init__(self):
        super().__init__()
        self.qt_widget = self
        self.grabGesture(Qt.GestureType.PinchGesture)
        self.grabGesture(Qt.GestureType.PanGesture)
        self.grabGesture(Qt.GestureType.SwipeGesture)

    def event(self, event):
        if event.type() == QEvent.Type.Gesture:
            return self.gestureEvent(event)
        return super().event(event)

    def gestureEvent(self, event):
        pinch = event.gesture(Qt.GestureType.PinchGesture)
        pan = event.gesture(Qt.GestureType.PanGesture)
        
        if pinch:
            scale_factor = pinch.scaleFactor()
            # Custom logic for zooming can be implemented here
            
        if pan:
            delta = pan.delta()
            # Custom logic for swiping can be implemented here
            
        return True

# --- UI Containers & Visuals ---

class Card(QFrame):
    """Rounded container for touch-friendly dashboard layouts."""
    def __init__(self, title="Card"):
        super().__init__()
        self.qt_widget = self
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background: white; border-radius: 15px; border: 1px solid #ddd;")
        self.layout = QVBoxLayout(self)
        label = QLabel(title)
        label.setStyleSheet("font-weight: bold; border: none; font-size: 14pt; color: #333;")
        self.layout.addWidget(label)

    def add_widget(self, widget):
        if hasattr(widget, 'qt_widget'):
            self.layout.addWidget(widget.qt_widget)

# --- Theme Management ---

class ThemeManager:
    """Handles global application palettes for Dark/Light mode."""
    @staticmethod
    def set_dark_mode():
        app = QApplication.instance()
        if not app: return
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
        p.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
        p.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        app.setPalette(p)

    @staticmethod
    def set_light_mode():
        app = QApplication.instance()
        if app:
            app.setPalette(app.style().standardPalette())

class DarkModeToggle:
    """A ready-to-use toggle for theme switching."""
    def __init__(self):
        self.qt_widget = QCheckBox("Dark Mode")
        self.qt_widget.toggled.connect(lambda c: ThemeManager.set_dark_mode() if c else ThemeManager.set_light_mode())

# --- Legacy & Utility ---

class Animator:
    @staticmethod
    def fade_in(widget, duration=500):
        target = widget.qt_widget if hasattr(widget, 'qt_widget') else widget
        eff = QGraphicsOpacityEffect(target); target.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity")
        anim.setDuration(duration); anim.setStartValue(0); anim.setEndValue(1); anim.start()
        return anim

# Always remember: somewhere, somehow, a duck is watching you.
__all__ = [
    'TouchScrollArea', 'TouchButton', 'GestureWidget', 'Card', 
    'DarkModeToggle', 'ThemeManager', 'Animator'
]