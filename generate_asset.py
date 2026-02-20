import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor, QPen, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QSize

def create_gear_image(output_path):
    # Image size
    width = 100
    height = 200
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    cx = width / 2
    cy = 20 # Top pivot area
    
    # 1. Main Strut (Top)
    painter.setBrush(QBrush(QColor("#B0BEC5"))) # Blue Grey
    painter.setPen(QPen(Qt.GlobalColor.black, 2))
    painter.drawRect(int(cx)-15, int(cy), 30, 80)
    
    # 2. Piston (Bottom, inner)
    painter.setBrush(QBrush(QColor("#ECEFF1"))) # Light Grey
    painter.drawRect(int(cx)-10, int(cy)+80, 20, 60)
    
    # 3. Wheel Axle
    painter.setBrush(QBrush(QColor("#37474F"))) # Dark Grey
    painter.drawEllipse(QPointF(cx, cy+140), 10, 10)
    
    # 4. Wheel
    painter.setBrush(QBrush(QColor("#212121"))) # Black Tire
    painter.drawEllipse(QPointF(cx, cy+140), 40, 40)
    
    # 5. Rim
    painter.setBrush(QBrush(QColor("#90A4AE"))) # Grey Rim
    painter.drawEllipse(QPointF(cx, cy+140), 20, 20)
    
    # 6. Pivot Point (Top)
    painter.setBrush(QBrush(QColor("#546E7A")))
    painter.drawEllipse(QPointF(cx, cy), 10, 10)
    
    painter.end()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if image.save(output_path):
        print(f"Successfully saved placeholder image to: {output_path}")
    else:
        print(f"Failed to save image to: {output_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Determine output path relative to script or CWD
    # We want it in gui/resources/gear_image.png relative to project root
    # Start from current working directory which should be project root
    output_path = os.path.join(os.getcwd(), "gui", "resources", "gear_image.png")
    
    create_gear_image(output_path)
