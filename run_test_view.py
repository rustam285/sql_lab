import sys
import logging
from PySide6.QtWidgets import QApplication
from src.view.main_window import MainWindow
from src.model.graph_model import GraphModel
from src.controller.app_controller import AppController

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Современный стиль
    
    win = MainWindow()
    model = GraphModel()
    controller = AppController(model, win.scene, win)
    
    win.show()
    sys.exit(app.exec())