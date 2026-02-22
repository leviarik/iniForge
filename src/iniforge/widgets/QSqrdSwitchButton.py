from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QBrush

class QSqrdSwitchButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(False)
        self.setFixedSize(30, 14)  # Fixed size with height 14 and width 30
        self.setStyleSheet("border: none;")  # Remove any default border
        self.update_stylesheet()

        self.clicked.connect(self.toggle_switch)

    def toggle_switch(self):
        self.update_stylesheet()

    def update_stylesheet(self):
        if self.isChecked():
            self.setStyleSheet("""
                CustomSwitch {
                    background-color: #666769;
                    border-radius: 0px; /* Ensure no border radius */
                    border: none;
                }
                CustomSwitch::indicator {
                    width: 12px;
                    height: 12px;
                    background-color: white;
                    border-radius: 0px; /* Ensure no border radius */
                    position: absolute;
                    right: 2px; /* Adjusted to align to the right */
                    top: 1px; /* Center vertically */
                    border: none;
                }
            """)
        else:
            self.setStyleSheet("""
                CustomSwitch {
                    background-color: #cccccc;
                    border-radius: 0px; /* Ensure no border radius */
                    border: none;
                }
                CustomSwitch::indicator {
                    width: 12px;
                    height: 12px;
                    background-color: white;
                    border-radius: 0px; /* Ensure no border radius */
                    position: absolute;
                    left: 1px; /* Adjusted to align to the left */
                    top: 1px; /* Center vertically */
                    border: none;
                }
            """)
        self.setFixedSize(30, 14)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(Qt.NoPen)
        painter.setPen(pen)
        
        rect = self.rect()
        if self.isChecked():
            brush = QBrush(QColor("#666769"))
        else:
            brush = QBrush(QColor("#cccccc"))
        
        painter.setBrush(brush)
        painter.drawRect(rect)  # Draw a rectangle instead of a rounded rectangle
        
        indicator_x = self.width() - self.height() - 2 if self.isChecked() else 1
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRect(indicator_x, 1, self.height() - 2, self.height() - 2)  # Draw a rectangle for the indicator
