import sys
import os
import traceback
import logging

from PyQt5.QtWidgets import QApplication, QMessageBox, QDesktopWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QCursor

from ui.importar_excel import ImportarExcel


# ==============================
# 🧠 CONFIGURAR LOGS
# ==============================
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ==============================
# 🧠 MANEJO GLOBAL DE ERRORES
# ==============================
def exception_hook(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))

    # guardar en log
    logging.error(error_msg)
    print(error_msg)

    # mostrar error sin crashear si QMessageBox falla
    try:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("❌ Error del Sistema")
        msg.setText("Ocurrió un error inesperado")
        msg.setDetailedText(error_msg)
        msg.exec_()
    except Exception:
        pass


# ==============================
# 🚀 FUNCIÓN PRINCIPAL
# ==============================
def main():
    sys.excepthook = exception_hook

    # High DPI para pantallas modernas (antes de crear QApplication)
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(getattr(Qt, "AA_EnableHighDpiScaling"), True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(getattr(Qt, "AA_UseHighDpiPixmaps"), True)

    app = QApplication(sys.argv)

    # ==============================
    # 🎨 ESTILO GLOBAL PRO
    # ==============================
    app.setStyle("Fusion")

    # fuente global más limpia
    app.setFont(QFont("Segoe UI", 10))

    app.setStyleSheet("""
        QWidget {
            background-color: #f5f6fa;
        }

        QLabel {
            color: #2c3e50;
        }

        QPushButton {
            background-color: #3498db;
            color: white;
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #2980b9;
        }

        QPushButton:pressed {
            background-color: #1f6dad;
        }

        QComboBox {
            padding: 5px;
            border-radius: 5px;
            background-color: white;
            border: 1px solid #dcdde1;
        }

        QLineEdit {
            padding: 5px;
            border-radius: 5px;
            background-color: white;
            border: 1px solid #dcdde1;
        }

        QScrollBar:vertical {
            background: #ecf0f1;
            width: 10px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical {
            background: #95a5a6;
            border-radius: 5px;
            min-height: 30px;
        }

        QScrollBar::handle:vertical:hover {
            background: #7f8c8d;
        }

        QScrollBar:horizontal {
            background: #ecf0f1;
            height: 10px;
            border-radius: 5px;
        }

        QScrollBar::handle:horizontal {
            background: #95a5a6;
            border-radius: 5px;
            min-width: 30px;
        }

        QScrollBar::handle:horizontal:hover {
            background: #7f8c8d;
        }

        QTableWidget {
            background-color: white;
            gridline-color: #dcdde1;
            border-radius: 6px;
        }

        QHeaderView::section {
            background-color: #3498db;
            color: white;
            padding: 8px;
            font-weight: bold;
        }

        QProgressBar {
            background-color: #ecf0f1;
            border-radius: 5px;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #3498db;
            border-radius: 5px;
        }
    """)

    # ==============================
    # 🖥 VENTANA PRINCIPAL
    # ==============================
    ventana = ImportarExcel()

    ventana.setMinimumSize(1100, 700)
    ventana.setWindowTitle("📊 Sistema Empresarial PRO MAX")

    # centrar ventana automáticamente (compatible multi-monitor)
    pantalla = QDesktopWidget().screenGeometry(QDesktopWidget().screenNumber(QCursor.pos()))
    x = (pantalla.width() - ventana.width()) // 2 + pantalla.left()
    y = (pantalla.height() - ventana.height()) // 2 + pantalla.top()
    ventana.move(x, y)

    ventana.show()

    return app.exec_()


# ==============================
# ▶️ EJECUCIÓN
# ==============================
if __name__ == "__main__":
    sys.exit(main())