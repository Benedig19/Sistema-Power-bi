from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QFileDialog,
    QTextEdit, QHBoxLayout, QStackedLayout, QLabel, QFrame, QScrollArea,
    QMessageBox, QProgressDialog, QComboBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from services.excel_service import leer_excel
from services.analytics import analizar_datos
from services.graficos import crear_grafico
from ui.dashboard import Dashboard


class ImportarExcel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 SISTEMA EMPRESARIAL PRO MAX")

        self.main_layout = QVBoxLayout()

        # =========================
        # 🧠 HEADER
        # =========================
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        h_layout = QVBoxLayout()

        titulo = QLabel("📊 SISTEMA DE ANÁLISIS EMPRESARIAL")
        titulo.setStyleSheet("color:white;font-size:16px;font-weight:bold;")

        subtitulo = QLabel("Carga, analiza y visualiza datos automáticamente")
        subtitulo.setStyleSheet("color:#bdc3c7;font-size:11px;")

        h_layout.addWidget(titulo)
        h_layout.addWidget(subtitulo)

        header.setLayout(h_layout)
        self.main_layout.addWidget(header)

        # =========================
        # 🔘 BOTONES + FILTRO DE GRÁFICO
        # =========================
        botones = QHBoxLayout()

        self.btn_cargar = self.crear_boton("📥 Cargar Excel")
        self.btn_cargar.clicked.connect(self.cargar_excel)

        self.btn_analisis = self.crear_boton("📄 Análisis")
        self.btn_analisis.clicked.connect(self.ver_analisis)

        self.btn_graficos = self.crear_boton("📊 Gráficos")
        self.btn_graficos.clicked.connect(self.generar_graficos)

        self.btn_dashboard = self.crear_boton("🖥 Dashboard")
        self.btn_dashboard.clicked.connect(self.ver_dashboard)

        # Selector de tipo de gráfico
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems([
            "🎯 Auto (recomendado)",
            "📊 Barras verticales", 
            "📊 Barras horizontales",
            "🥧 Pastel / Donut",
            "📈 Líneas",
            "🗻 Área"
        ])
        self.combo_tipo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border-radius: 6px;
                background-color: #1f2d3d;
                color: white;
                min-width: 180px;
            }
        """)

        botones.addWidget(self.btn_cargar)
        botones.addWidget(self.btn_analisis)
        botones.addWidget(self.btn_graficos)
        botones.addWidget(self.btn_dashboard)
        botones.addStretch()
        botones.addWidget(QLabel("Tipo:"))
        botones.addWidget(self.combo_tipo)

        self.main_layout.addLayout(botones)

        # =========================
        # STACK
        # =========================
        self.stack = QStackedLayout()

        # ANALISIS
        self.vista_analisis = QWidget()
        a_layout = QVBoxLayout()

        self.texto = QTextEdit()
        self.texto.setReadOnly(True)

        a_layout.addWidget(self.texto)
        self.vista_analisis.setLayout(a_layout)

        # GRÁFICOS
        self.vista_graficos = QWidget()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.container = QWidget()
        self.layout_graficos = QVBoxLayout()
        self.layout_graficos.setSpacing(20)

        self.container.setLayout(self.layout_graficos)
        self.scroll.setWidget(self.container)

        g_layout = QVBoxLayout()
        g_layout.addWidget(self.scroll)

        self.vista_graficos.setLayout(g_layout)

        self.stack.addWidget(self.vista_analisis)
        self.stack.addWidget(self.vista_graficos)

        self.main_layout.addLayout(self.stack)
        self.setLayout(self.main_layout)

        self.resultado = None

    # =========================
    # 🎨 BOTÓN
    # =========================
    def crear_boton(self, texto):
        btn = QPushButton(texto)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1f2d3d;
                color: white;
                padding: 8px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        return btn

    # =========================
    # 📥 CARGAR EXCEL
    # =========================
    def cargar_excel(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Excel", "", 
            "Excel (*.xlsx *.xls);;Todos los archivos (*)"
        )

        if not archivo:
            return

        progress = QProgressDialog("Cargando Excel...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)  # type: ignore[attr-defined]
        progress.setCancelButton(None)
        progress.show()

        try:
            df = leer_excel(archivo)
            progress.close()

            if df is None or df.empty:
                self.texto.setText("❌ No se pudo leer el Excel o está vacío")
                QMessageBox.warning(self, "Error", "❌ El archivo está vacío o no es válido")
                return

            self.resultado = analizar_datos(df)

            salida = f"📊 ANÁLISIS EMPRESARIAL\n"
            salida += f"📁 Archivo: {archivo.split('/')[-1].split(chr(92))[-1]}\n"
            salida += f"📈 {len(df)} filas x {len(df.columns)} columnas\n\n"

            for item in self.resultado.get("analisis", []):

                tipo = item.get("tipo", "texto")
                col = item.get("columna", "Desconocido")

                if tipo == "numérico":
                    salida += f"[NUM] {col}\n"
                    salida += f"  Total: {item.get('total', 0):,.2f}\n"
                    salida += f"  Promedio: {item.get('promedio', 0):,.2f}\n"
                    salida += f"  Mín: {item.get('min', 0):,.2f}\n"
                    salida += f"  Máx: {item.get('max', 0):,.2f}\n\n"

                elif tipo == "fecha":
                    salida += f"[FECHA] {col}\n"
                    salida += f"  Desde: {item.get('min', 'N/A')}\n"
                    salida += f"  Hasta: {item.get('max', 'N/A')}\n"
                    salida += f"  Únicos: {item.get('unicos', 0)}\n\n"

                else:
                    salida += f"[{tipo.upper()}] {col}\n"
                    top = item.get("top", {})
                    for k, v in list(top.items())[:5]:
                        salida += f"  {k}: {v}\n"
                    if len(top) > 5:
                        salida += f"  ... y {len(top) - 5} más\n"
                    salida += "\n"

            self.texto.setText(salida)
            self.stack.setCurrentIndex(0)
            QMessageBox.information(self, "Éxito", f"✅ {len(df)} filas cargadas correctamente")

        except Exception as e:
            progress.close()
            self.texto.setText(f"❌ Error al cargar:\n{str(e)}")
            QMessageBox.critical(self, "Error", f"❌ No se pudo cargar el archivo:\n{str(e)}")

    # =========================
    # 📊 GRÁFICOS CON 5 TIPOS
    # =========================
    def generar_graficos(self):

        if not self.resultado:
            QMessageBox.warning(self, "Atención", "⚠️ Primero carga un Excel")
            self.stack.setCurrentIndex(0)
            return

        # limpiar correctamente
        while self.layout_graficos.count():
            item = self.layout_graficos.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget:
                widget.deleteLater()

        tipo_seleccionado = self.combo_tipo.currentText()
        graficos = 0

        for item in self.resultado.get("analisis", []):

            top = item.get("top")
            if not top or not isinstance(top, dict) or len(top) == 0:
                continue

            try:
                # Detectar tipo automático o usar el seleccionado
                tipo = self._detectar_tipo(tipo_seleccionado, item, top)

                fig = crear_grafico(top, item.get("columna", "Gráfico"), tipo=tipo)
                canvas = FigureCanvas(fig)
                canvas.setFixedHeight(350)

                # Info del tipo usado
                info = QLabel(f"📊 {item.get('columna', '')} — {tipo.upper()}")
                info.setStyleSheet("color: #bdc3c7; font-size: 11px; padding: 4px;")

                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: #1e293b;
                        border-radius: 10px;
                        border: 1px solid #334155;
                        padding: 10px;
                    }
                """)
                card_layout = QVBoxLayout(card)
                card_layout.addWidget(info)
                card_layout.addWidget(canvas)

                self.layout_graficos.addWidget(card)
                graficos += 1

            except Exception as e:
                print(f"Error gráfico {item.get('columna')}: {e}")

        if graficos == 0:
            aviso = QTextEdit("⚠️ No hay datos categóricos para gráficos")
            self.layout_graficos.addWidget(aviso)

        self.stack.setCurrentIndex(1)

    def _detectar_tipo(self, seleccionado, item, top):
        """Detecta el mejor tipo de gráfico según los datos."""
        # Si el usuario eligió algo específico, usarlo
        if "Barras verticales" in seleccionado:
            return "barras"
        elif "Barras horizontales" in seleccionado:
            return "barras_h"
        elif "Pastel" in seleccionado or "Donut" in seleccionado:
            return "pastel"
        elif "Líneas" in seleccionado:
            return "lineas"
        elif "Área" in seleccionado:
            return "area"

        # AUTO: detectar según características de los datos
        cantidad = len(top)

        # Si son fechas o tienen orden natural → líneas o área
        if item.get("tipo") == "fecha" or cantidad >= 10:
            return "lineas"

        # Si son pocas categorías → pastel
        if cantidad <= 6:
            return "pastel"

        # Si son valores muy desiguales → barras horizontales
        valores = list(top.values())
        try:
            nums = [float(v) for v in valores]
            if max(nums) > sum(nums) * 0.5:  # Un valor domina
                return "barras_h"
        except:
            pass

        # Por defecto → barras verticales
        return "barras"

    # =========================
    # 🖥 DASHBOARD
    # =========================
    def ver_dashboard(self):
        if not self.resultado:
            QMessageBox.warning(self, "Atención", "⚠️ Primero carga un Excel")
            return

        self.ventana_dashboard = Dashboard(self.resultado)
        self.ventana_dashboard.show()

    # =========================
    # 📄 ANALISIS
    # =========================
    def ver_analisis(self):
        if self.resultado:
            self.stack.setCurrentIndex(0)