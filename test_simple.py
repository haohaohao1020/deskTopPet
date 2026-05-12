import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QBrush, QPen

class SimplePet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(120, 120)
        self.move(500, 300)
        print("SimplePet created")
    
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        p.setBrush(QBrush(QColor(255, 200, 150)))
        p.setPen(QPen(QColor(200, 150, 100), 2))
        p.drawEllipse(10, 30, 100, 80)
        p.drawEllipse(15, 5, 90, 70)
        
        p.setBrush(QBrush(QColor(80, 80, 120)))
        p.drawEllipse(35, 25, 12, 14)
        p.drawEllipse(73, 25, 12, 14)
        
        p.end()
        print("paintEvent called")

def main():
    print("Starting test...")
    app = QApplication(sys.argv)
    print("QApplication created")
    
    pet = SimplePet()
    print("Showing pet...")
    pet.show()
    
    print("Entering event loop...")
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
