import sys
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen

def create_app_icon():
    pix = QPixmap(64, 64)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QBrush(QColor(255, 200, 150)))
    p.setPen(QPen(QColor(200, 150, 100), 2))
    p.drawEllipse(10, 15, 44, 44)
    p.drawEllipse(14, 5, 36, 32)
    p.end()
    return QIcon(pix)

def main():
    print("=" * 60)
    print("桌面宠物启动中...")
    print("=" * 60)
    
    app = None
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("桌面宠物")
        app.setApplicationDisplayName("桌面宠物")
        app.setWindowIcon(create_app_icon())
        print(f"[OK] QApplication created: {app}")
        
        print("[INFO] Importing pet_window...")
        from pet_window import PetWindow
        print("[OK] pet_window imported")
        
        print("[INFO] Creating PetWindow...")
        window = PetWindow(app)
        print("[OK] PetWindow created")
        
        print("[INFO] Showing window...")
        window.show()
        print("[OK] Window shown")
        
        print("[INFO] Entering event loop...")
        print("=" * 60)
        return app.exec()
    except Exception as e:
        print(f"[ERROR] Fatal: {e}")
        traceback.print_exc()
        if app:
            QMessageBox.critical(
                None,
                "启动错误",
                f"启动失败:\n\n{e}\n\n详情请查看控制台输出"
            )
        return 1

if __name__ == "__main__":
    sys.exit(main())
