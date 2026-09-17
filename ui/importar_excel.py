
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, cast

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedLayout,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services.analytics import analizar_datos
from services.excel_service import leer_excel
from services.graficos import crear_grafico
from ui.dashboard import Dashboard


# =============================================================================
# TEMA / ESTILOS CENTRALIZADOS
# =============================================================================

TEMA = {
    "fondo_header": "#2c3e50",
    "fondo_boton": "#1f2d3d",
    "fondo_boton_hover": "#34495e",
    "fondo_card": "#1e293b",
    "borde_card": "#334155",
    "texto_claro": "#ffffff",
    "texto_secundario": "#bdc3c7",
    "texto_tenue": "#94a3b8",
}

QSS_BOTON = f"""
    QPushButton {{
        background-color: {TEMA['fondo_boton']};
        color: {TEMA['texto_claro']};
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 12px;
    }}
    QPushButton:hover {{ background-color: {TEMA['fondo_boton_hover']}; }}
    QPushButton:pressed {{ background-color: #2c3e50; }}
"""

QSS_HEADER = f"""
    QFrame {{
        background-color: {TEMA['fondo_header']};
        border-radius: 10px;
        padding: 10px;
    }}
"""

QSS_COMBO = f"""
    QComboBox {{
        padding: 6px 10px;
        border-radius: 6px;
        background-color: {TEMA['fondo_boton']};
        color: {TEMA['texto_claro']};
        min-width: 190px;
    }}
"""

QSS_CARD = f"""
    QFrame {{
        background-color: {TEMA['fondo_card']};
        border-radius: 10px;
        border: 1px solid {TEMA['borde_card']};
        padding: 10px;
    }}
"""

# Tipos de grafico: (texto visible, valor interno). El valor interno
# es lo que se guarda como userData del combo, asi no dependemos del
# texto (que trae emoji y podria traducirse).
TIPOS_GRAFICO = [
    ("🎯 Auto (recomendado)", "auto"),
    ("📊 Barras verticales", "barras"),
    ("📊 Barras horizontales", "barras_h"),
    ("🥧 Pastel / Donut", "pastel"),
    ("📈 Líneas", "lineas"),
    ("🗻 Área", "area"),
]


# =============================================================================
# WORKER: lee y analiza el Excel en un hilo aparte
# =============================================================================

class _CargaExcelWorker(QThread):
    """Ejecuta `leer_excel` + `analizar_datos` fuera del hilo de la UI.

    Sin esto, un Excel grande congela toda la ventana mientras se lee
    (el QProgressDialog original giraba solo porque Qt reprocesaba
    eventos entre llamadas cortas; con archivos pesados se queda
    pegado). Emite `terminado(df, resultado)` en exito o
    `fallo(mensaje)` si algo lanza una excepcion.
    """

    terminado = pyqtSignal(object, dict)
    fallo = pyqtSignal(str)

    def __init__(self, ruta_archivo: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.ruta_archivo = ruta_archivo

    def run(self) -> None:  # noqa: D102
        try:
            df = leer_excel(self.ruta_archivo)
            if df is None or df.empty:
                self.fallo.emit("El archivo está vacío o no es válido.")
                return
            resultado = analizar_datos(df)
            self.terminado.emit(df, resultado)
        except Exception as exc:  # noqa: BLE001
            self.fallo.emit(str(exc))


# =============================================================================
# WIDGET PRINCIPAL
# =============================================================================

class ImportarExcel(QWidget):
    """Pantalla principal: cargar Excel, ver análisis en texto, ver
    gráficos por categoría y abrir el dashboard."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sistema Empresarial Pro Max")
        self.setMinimumSize(900, 620)

        self.resultado: Optional[Dict[str, Any]] = None
        self.df_actual: Optional[pd.DataFrame] = None
        self._worker: Optional[_CargaExcelWorker] = None
        self._progress: Optional[QProgressDialog] = None
        # Referencias vivas a ventanas de Dashboard abiertas, para que
        # PyQt no las destruya apenas termina ver_dashboard().
        self._dashboards: List[Dashboard] = []

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self._build_header())
        self.main_layout.addLayout(self._build_toolbar())
        self.main_layout.addLayout(self._build_stack())

    # -------------------------------------------------------------------
    # CONSTRUCCION DE LA UI
    # -------------------------------------------------------------------

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setStyleSheet(QSS_HEADER)

        titulo = QLabel("📊 SISTEMA DE ANÁLISIS EMPRESARIAL")
        titulo.setStyleSheet(f"color:{TEMA['texto_claro']};font-size:16px;font-weight:bold;")

        subtitulo = QLabel("Carga, analiza y visualiza datos automáticamente")
        subtitulo.setStyleSheet(f"color:{TEMA['texto_secundario']};font-size:11px;")

        layout = QVBoxLayout(header)
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        return header

    def _build_toolbar(self) -> QHBoxLayout:
        botones = QHBoxLayout()

        self.btn_cargar = self._crear_boton("📥 Cargar Excel")
        self.btn_cargar.clicked.connect(self.cargar_excel)

        self.btn_analisis = self._crear_boton("📄 Análisis")
        self.btn_analisis.clicked.connect(self.ver_analisis)

        self.btn_graficos = self._crear_boton("📊 Gráficos")
        self.btn_graficos.clicked.connect(self.generar_graficos)

        self.btn_dashboard = self._crear_boton("🖥 Dashboard")
        self.btn_dashboard.clicked.connect(self.ver_dashboard)

        self.combo_tipo = QComboBox()
        self.combo_tipo.setStyleSheet(QSS_COMBO)
        for texto, valor in TIPOS_GRAFICO:
            self.combo_tipo.addItem(texto, userData=valor)

        botones.addWidget(self.btn_cargar)
        botones.addWidget(self.btn_analisis)
        botones.addWidget(self.btn_graficos)
        botones.addWidget(self.btn_dashboard)
        botones.addStretch()
        botones.addWidget(QLabel("Tipo:"))
        botones.addWidget(self.combo_tipo)
        return botones

    def _build_stack(self) -> QStackedLayout:
        self.stack = QStackedLayout()
        self.stack.addWidget(self._build_vista_analisis())
        self.stack.addWidget(self._build_vista_graficos())
        return self.stack

    def _build_vista_analisis(self) -> QWidget:
        vista = QWidget()
        layout = QVBoxLayout(vista)

        self.texto = QTextEdit()
        self.texto.setReadOnly(True)
        self.texto.setStyleSheet(f"background-color:{TEMA['fondo_card']}; color:{TEMA['texto_claro']};")

        layout.addWidget(self.texto)
        return vista

    def _build_vista_graficos(self) -> QWidget:
        vista = QWidget()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.container = QWidget()
        self.layout_graficos = QVBoxLayout(self.container)
        self.layout_graficos.setSpacing(20)
        self.layout_graficos.addStretch()  # empuja las tarjetas hacia arriba

        self.scroll.setWidget(self.container)

        layout = QVBoxLayout(vista)
        layout.addWidget(self.scroll)
        return vista

    def _crear_boton(self, texto: str) -> QPushButton:
        btn = QPushButton(texto)
        btn.setStyleSheet(QSS_BOTON)
        btn.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        return btn

    # -------------------------------------------------------------------
    # CARGAR EXCEL (en segundo plano)
    # -------------------------------------------------------------------

    def cargar_excel(self) -> None:
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Excel", "",
            "Excel (*.xlsx *.xls);;Todos los archivos (*)",
        )
        if not archivo:
            return

        self._progress = QProgressDialog("Cargando y analizando Excel...", None, 0, 0, self)
        self._progress.setWindowModality(Qt.WindowModal)  # type: ignore[attr-defined]
        self._progress.setCancelButton(None)
        self._progress.setMinimumDuration(0)
        self._progress.show()

        # Deshabilitar botones mientras carga, para evitar doble click
        self._set_botones_habilitados(False)

        self._worker = _CargaExcelWorker(archivo, self)
        self._worker.terminado.connect(lambda df, resultado: self._on_carga_ok(archivo, df, resultado))
        self._worker.fallo.connect(self._on_carga_error)
        self._worker.finished.connect(self._cerrar_progreso)
        self._worker.start()

    def _set_botones_habilitados(self, habilitado: bool) -> None:
        for btn in (self.btn_cargar, self.btn_analisis, self.btn_graficos, self.btn_dashboard):
            btn.setEnabled(habilitado)

    def _cerrar_progreso(self) -> None:
        if self._progress:
            self._progress.close()
            self._progress = None
        self._set_botones_habilitados(True)

    def _on_carga_ok(self, archivo: str, df: pd.DataFrame, resultado: Dict[str, Any]) -> None:
        self.df_actual = df
        self.resultado = resultado
        self.texto.setText(self._formatear_resumen(archivo, df, resultado))
        self.stack.setCurrentIndex(0)
        QMessageBox.information(self, "Éxito", f"✅ {len(df)} filas cargadas correctamente")

    def _on_carga_error(self, mensaje: str) -> None:
        self.texto.setText(f"❌ Error al cargar:\n{mensaje}")
        QMessageBox.critical(self, "Error", f"❌ No se pudo cargar el archivo:\n{mensaje}")

    @staticmethod
    def _formatear_resumen(archivo: str, df: pd.DataFrame, resultado: Dict[str, Any]) -> str:
        """Arma el texto de resumen del analisis. Separado en su propio
        metodo (y estatico) para poder probarlo sin instanciar la UI."""
        partes = [
            "📊 ANÁLISIS EMPRESARIAL",
            f"📁 Archivo: {os.path.basename(archivo)}",
            f"📈 {len(df)} filas x {len(df.columns)} columnas",
            "",
        ]

        for item in resultado.get("analisis", []):
            tipo = item.get("tipo", "texto")
            col = item.get("columna", "Desconocido")

            if tipo == "numérico":
                partes += [
                    f"[NUM] {col}",
                    f"  Total: {item.get('total', 0):,.2f}",
                    f"  Promedio: {item.get('promedio', 0):,.2f}",
                    f"  Mín: {item.get('min', 0):,.2f}",
                    f"  Máx: {item.get('max', 0):,.2f}",
                    "",
                ]
            elif tipo == "fecha":
                partes += [
                    f"[FECHA] {col}",
                    f"  Desde: {item.get('min', 'N/A')}",
                    f"  Hasta: {item.get('max', 'N/A')}",
                    f"  Únicos: {item.get('unicos', 0)}",
                    "",
                ]
            else:
                partes.append(f"[{tipo.upper()}] {col}")
                top = item.get("top", {})
                for k, v in list(top.items())[:5]:
                    partes.append(f"  {k}: {v}")
                if len(top) > 5:
                    partes.append(f"  ... y {len(top) - 5} más")
                partes.append("")

        return "\n".join(partes)

    # -------------------------------------------------------------------
    # GRAFICOS
    # -------------------------------------------------------------------

    def generar_graficos(self) -> None:
        if not self.resultado:
            QMessageBox.warning(self, "Atención", "⚠️ Primero carga un Excel")
            self.stack.setCurrentIndex(0)
            return

        self._limpiar_graficos()

        tipo_valor = cast(str, self.combo_tipo.currentData() or "auto")
        graficos_creados = 0

        for item in self.resultado.get("analisis", []):
            top = item.get("top")
            if not isinstance(top, dict) or not top:
                continue

            columna = item.get("columna", "Gráfico")
            tarjeta = self._crear_tarjeta_grafico(item, top, tipo_valor, columna)
            # Insertar antes del "stretch" final para que las tarjetas
            # queden arriba y no se separen entre si.
            self.layout_graficos.insertWidget(self.layout_graficos.count() - 1, tarjeta)
            graficos_creados += 1

        if graficos_creados == 0:
            aviso = QLabel("⚠️ No hay datos categóricos para generar gráficos")
            aviso.setStyleSheet(f"color:{TEMA['texto_tenue']}; padding: 20px;")
            aviso.setAlignment(Qt.AlignCenter)  # type: ignore[attr-defined]
            self.layout_graficos.insertWidget(0, aviso)

        self.stack.setCurrentIndex(1)

    def _crear_tarjeta_grafico(self, item: Dict[str, Any], top: Dict[str, Any],
                                tipo_valor: str, columna: str) -> QFrame:
        """Crea la tarjeta (card) de un grafico individual. Si falla la
        generacion, la tarjeta muestra el error en vez de perderse en
        la consola (como hacia el `print` original)."""
        card = QFrame()
        card.setStyleSheet(QSS_CARD)
        card_layout = QVBoxLayout(card)

        try:
            tipo_final = self._detectar_tipo(tipo_valor, item, top)
            fig = crear_grafico(top, columna, tipo=tipo_final)

            canvas = FigureCanvas(fig)
            canvas.setFixedHeight(350)
            canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            # Clave para evitar fugas de memoria: FigureCanvasQTAgg ya
            # tiene su propia referencia a `fig`, asi que podemos
            # cerrarla en el registro global de matplotlib/pyplot sin
            # que desaparezca del canvas.
            plt.close(fig)

            info = QLabel(f"📊 {columna} — {tipo_final.upper()}")
            info.setStyleSheet(f"color:{TEMA['texto_secundario']}; font-size:11px; padding:4px;")

            card_layout.addWidget(info)
            card_layout.addWidget(canvas)

        except Exception as exc:  # noqa: BLE001
            error_lbl = QLabel(f"❌ No se pudo graficar '{columna}':\n{exc}")
            error_lbl.setStyleSheet("color:#ef4444; padding: 10px;")
            error_lbl.setWordWrap(True)
            card_layout.addWidget(error_lbl)

        return card

    def _limpiar_graficos(self) -> None:
        """Elimina las tarjetas y conserva el ``stretch`` final.

        ``QLayoutItem.widget()`` y ``QLayoutItem.layout()`` pueden devolver
        ``None``. Además, un ``QLayout`` no debe eliminarse llamando a
        ``deleteLater``: primero hay que vaciar sus hijos.
        """
        while self.layout_graficos.count() > 1:
            item = self.layout_graficos.takeAt(0)

            # Según los stubs de PyQt, takeAt() puede devolver None.
            # No se debe acceder a widget() o layout() sin comprobarlo.
            if item is None:
                continue

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                continue

            child_layout = item.layout()
            if child_layout is not None:
                self._limpiar_layout(child_layout)

    @staticmethod
    def _limpiar_layout(layout: QLayout) -> None:
        """Limpia recursivamente un layout secundario de Qt."""
        while layout.count() > 0:
            item = layout.takeAt(0)

            if item is None:
                continue

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                continue

            child_layout = item.layout()
            if child_layout is not None:
                ImportarExcel._limpiar_layout(child_layout)

    @staticmethod
    def _detectar_tipo(tipo_valor: str, item: Dict[str, Any], top: Dict[str, Any]) -> str:
        """Devuelve el tipo de grafico a usar. `tipo_valor` viene del
        userData del combo ("auto", "barras", "pastel", ...), ya no de
        parsear el texto visible con emojis."""
        if tipo_valor and tipo_valor != "auto":
            return tipo_valor

        # ---- modo AUTO: heuristica segun los datos ----
        cantidad = len(top)

        if item.get("tipo") == "fecha" or cantidad >= 10:
            return "lineas"

        if cantidad <= 6:
            return "pastel"

        try:
            nums = [float(v) for v in top.values()]
            if nums and max(nums) > sum(nums) * 0.5:  # un valor domina el resto
                return "barras_h"
        except (TypeError, ValueError):
            pass

        return "barras"

    # -------------------------------------------------------------------
    # NAVEGACION
    # -------------------------------------------------------------------

    def ver_dashboard(self) -> None:
        if not self.resultado:
            QMessageBox.warning(self, "Atención", "⚠️ Primero carga un Excel")
            return

        ventana = Dashboard(self.resultado)
        self._dashboards.append(ventana)  # evita que el GC la cierre sola
        ventana.show()

    def ver_analisis(self) -> None:
        if self.resultado:
            self.stack.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "Atención", "⚠️ Primero carga un Excel")