from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QToolButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QRectF, QSize
from PySide6.QtGui import QPainter, QColor


class Slider(QWidget):
    """Inner slider that paints the track and knob."""
    toggled = Signal(bool)

    def __init__(self, width=50, height=20, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        palette = self.palette()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Theme colors
        color_on = QColor("#DC5801")   # ON highlight
        color_off = QColor("#8D0F70")  # OFF highlight

        base = palette.base().color()
        knob_color = palette.window().color() if base.lightness() < 128 else QColor("white")

        # Track
        track_rect = QRectF(0, 0, self.width(), self.height())
        track_color = color_on if self._checked else color_off
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, self.height() / 2, self.height() / 2)

        # Knob
        knob_size = self.height() - 4
        knob_x = self.width() - knob_size - 2 if self._checked else 2
        knob_rect = QRectF(knob_x, 2, knob_size, knob_size)
        painter.setBrush(knob_color)
        painter.drawEllipse(knob_rect)

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()

    def is_checked(self):
        return self._checked

    def set_checked(self, value: bool):
        self._checked = value
        self.update()


class ToggleSwitch(QWidget):
    """Boolean toggle with labels outside the slider."""
    toggled = Signal(bool)

    def __init__(self, label_off="STD", label_on="CoV", parent=None):
        super().__init__(parent)
        self.label_off = label_off
        self.label_on = label_on

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        self.left_label = QLabel(self.label_off)
        self.left_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        layout.addWidget(self.left_label)

        self.slider = Slider()
        self.slider.toggled.connect(self._emit_signal)
        layout.addWidget(self.slider)

        self.right_label = QLabel(self.label_on)
        self.right_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        layout.addWidget(self.right_label)

    def _emit_signal(self, state):
        self.toggled.emit(state)

    def is_checked(self):
        return self.slider.is_checked()

    def set_checked(self, value: bool):
        self.slider.set_checked(value)

    def value(self) -> str:
        return self.label_on if self.slider.is_checked() else self.label_off

    def set_labels(self, label_on: str, label_off: str):
        self.label_on = label_on
        self.label_off = label_off
        self.left_label.setText(label_off)
        self.right_label.setText(label_on)


class CollapsibleBox(QWidget):
    """Collapsible box that adapts to theme colors."""
    def __init__(self, title="", parent=None, title_font_size=12, arrow_size=10):
        super().__init__(parent)

        self.toggle_button = QToolButton(text=title, checkable=True, checked=True)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.DownArrow)
        self.toggle_button.setIconSize(QSize(arrow_size, arrow_size))
        self.toggle_button.setStyleSheet(f"""
            QToolButton {{
                border: none;
                font-weight: bold;
                font-size: {title_font_size}pt;
                padding: 5px;
            }}
        """)
        self.toggle_button.clicked.connect(self.on_toggle)

        # Background frame uses palette colors
        self.bg_frame = QFrame()
        self.bg_frame.setAutoFillBackground(True)
        self.update_bg_color()

        self.content_container = QWidget(self.bg_frame)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(5)
        self.content_layout = content_layout

        frame_layout = QVBoxLayout(self.bg_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(self.content_container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.toggle_button)
        main_layout.addWidget(self.bg_frame)

        self._expanded = True

    def update_bg_color(self):
        """Set background color dynamically based on theme."""
        palette = self.palette()
        bg = palette.alternateBase().color()
        self.bg_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg.name()};
                border-radius: 8px;
            }}
        """)

    def on_toggle(self):
        self._expanded = not self._expanded
        self.bg_frame.setVisible(self._expanded)
        self.toggle_button.setArrowType(Qt.DownArrow if self._expanded else Qt.RightArrow)

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)
