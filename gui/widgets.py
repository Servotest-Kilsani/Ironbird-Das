from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from PyQt6.QtCore import Qt, QSize, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QPixmap

class LEDIndicator(QWidget):
    def __init__(self, color=Qt.GlobalColor.green, size=20):
        super().__init__()
        self.color = color
        self.size = size
        self.state = False
        self.setFixedSize(size, size)

    def set_state(self, on):
        self.state = on
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.state:
            brush_color = self.color
        else:
            brush_color = Qt.GlobalColor.gray
            
        painter.setBrush(QBrush(brush_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.size, self.size)

class DigitalMeter(QWidget):
    def __init__(self, title, unit):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 10px; color: gray;")
        
        self.value_label = QLabel("0.00")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-size: 16px; font-weight: bold; border: 1px solid gray; background: black; color: #00FF00;")
        
        self.unit_label = QLabel(unit)
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.unit_label.setStyleSheet("font-size: 10px;")
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.unit_label)
        self.setLayout(layout)

    def set_value(self, value):
        self.value_label.setText(f"{value:.2f}")

class GearVisualizer(QWidget):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.angle = 0.0 # 0=Down (Vertical), 90=Up (Horizontal)
        self.setMinimumSize(150, 200)
        
        layout = QVBoxLayout()
        self.label = QLabel(name)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        layout.addStretch()
        self.setLayout(layout)
        
        # Load Image
        # Use absolute path relative to this file to avoid CWD issues
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # gui/widgets.py -> gui/ -> gui/resources/gear_image.png
        self.image_path = os.path.join(current_dir, "resources", "gear_image.png")
        
        print(f"[GearVisualizer] Looking for image at: {self.image_path}")
        self.pixmap = QPixmap(self.image_path)
        
        if self.pixmap.isNull():
            print(f"[GearVisualizer] Failed to load image. File exists? {os.path.exists(self.image_path)}")
        else:
             print(f"[GearVisualizer] Image loaded successfully. Size: {self.pixmap.width()}x{self.pixmap.height()}")

    def set_angle(self, angle):
        self.angle = angle
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        w = self.width()
        h = self.height()
        cx = w / 2
        cy = 40 # Pivot point near top
        
        # Draw Pivot Point (Debug or Visual aid)
        painter.setBrush(Qt.GlobalColor.darkGray)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), 5, 5)
        
        painter.save()
        painter.translate(cx, cy)
        # Rotate: 0 deg = Down. -90 deg = Right/Up.
        painter.rotate(-self.angle)
        
        if not self.pixmap.isNull():
            # Scale pixmap to fit reasonable height, e.g., 120px
            target_height = 120
            scaled_pixmap = self.pixmap.scaledToHeight(target_height, Qt.TransformationMode.SmoothTransformation)
            pw = scaled_pixmap.width()
            ph = scaled_pixmap.height()
            
            # Draw such that (0,0) is the pivot point (top center of gear)
            # Assuming the image top-center corresponds to the pivot
            painter.drawPixmap(-pw//2, 0, scaled_pixmap)
        else:
            # Fallback drawing if image missing
            pen = QPen(Qt.GlobalColor.darkGray)
            pen.setWidth(8)
            painter.setPen(pen)
            painter.drawLine(0, 0, 0, 80)
            painter.setBrush(Qt.GlobalColor.black)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(0, 80), 15, 15)
            painter.setPen(Qt.GlobalColor.red)
            painter.drawText(-30, 0, "No Image")

        painter.restore()
        
        # Draw Angle Text
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(int(cx)-20, int(h)-10, f"{self.angle:.1f}°")
