
from __future__ import annotations

import logging
import os
import tempfile
import textwrap
import traceback
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, cast

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image as PILImage

import reportlab.platypus as rl
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as pdf_canvas

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


# =============================================================================
# CONFIGURACION CENTRAL
# =============================================================================

PALETA = {
    "fondo": "#0f172a",
    "fondo_card": "#1e293b",
    "acento": "#3b82f6",
    "exito": "#10b981",
    "alerta": "#f59e0b",
    "peligro": "#ef4444",
    "morado": "#8b5cf6",
    "rosa": "#ec4899",
    "info": "#06b6d4",
    "texto": "#f8fafc",
    "texto_secundario": "#94a3b8",
    "borde": "#334155",
}

COLORES_GRAFICOS = [
    "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
    "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#64748b",
    "#a855f7", "#14b8a6", "#f43f5e", "#22c55e", "#eab308",
]

# Nota: se evitan emojis (📊,💎,🥇...) porque las fuentes base de
# ReportLab (Helvetica) no tienen esos glifos y se ven como cuadros
# vacios ("tofu") en el PDF. Se usan textos/simbolos compatibles con
# WinAnsiEncoding en su lugar.
MEDALLAS = ["1°", "2°", "3°"]


@dataclass
class ConfigReporte:
    """Configuracion central del reporte: tamano de hoja, margenes y dpi.

    Cambiar `orientacion` o `tamano_hoja` aqui es suficiente para ajustar
    todo el layout: las tablas y los graficos se recalculan en funcion
    del ancho de contenido disponible (`ancho_util`).
    """

    tamano_hoja: Tuple[float, float] = letter
    orientacion: str = "landscape"        # "landscape" o "portrait"
    margen: float = 1.1 * cm
    dpi: int = 150
    titulo_empresa: str = "Dashboard Analytics Pro"
    subtitulo_reporte: str = "Reporte Empresarial"

    @property
    def pagesize(self) -> Tuple[float, float]:
        base = self.tamano_hoja
        return landscape(base) if self.orientacion == "landscape" else base

    @property
    def ancho_util(self) -> float:
        """Ancho de contenido disponible en puntos (pagina - margenes)."""
        return self.pagesize[0] - 2 * self.margen

    @property
    def alto_util(self) -> float:
        return self.pagesize[1] - 2 * self.margen


# =============================================================================
# UTILIDADES
# =============================================================================

def _pct(valor: float, total: float) -> float:
    """Porcentaje seguro (evita division entre cero)."""
    return (valor / total * 100.0) if total else 0.0


def _top_items(data: Dict[str, float], n: int) -> Tuple[List[str], List[float], float]:
    """Ordena `data` de mayor a menor, recorta a los `n` primeros y
    devuelve etiquetas, valores y el total de TODO el diccionario original
    (no solo del recorte), para que el % refleje el peso real."""
    ordenado = OrderedDict(sorted(data.items(), key=lambda x: x[1], reverse=True))
    total_general = sum(float(v) for v in data.values())
    labels = list(ordenado.keys())[:n]
    values = [float(v) for v in list(ordenado.values())[:n]]
    return labels, values, total_general


def _envolver_etiqueta(texto: str, ancho: int = 14) -> str:
    """Corta etiquetas largas en varias lineas para que no se encimen
    en los ejes de los graficos."""
    return "\n".join(textwrap.wrap(str(texto), ancho)) or str(texto)


def _tamano_imagen_proporcional(ruta: str, ancho_max: float, alto_max: float) -> Tuple[float, float]:
    """Calcula (ancho, alto) en puntos para insertar la imagen `ruta`
    respetando su relacion de aspecto real, sin sobrepasar los maximos
    dados. Evita imagenes estiradas/deformadas."""
    with PILImage.open(ruta) as img:
        w_px, h_px = img.size
    ratio = w_px / h_px
    ancho, alto = ancho_max, ancho_max / ratio
    if alto > alto_max:
        alto = alto_max
        ancho = alto * ratio
    return ancho, alto


# =============================================================================
# GENERADOR DE GRAFICOS
# =============================================================================

class GraficoGenerator:
    """Genera los distintos tipos de graficos como imagenes PNG.

    Todos los metodos publicos devuelven la ruta del PNG generado, o
    None si `data` viene vacio o si ocurre un error (queda registrado
    en el log, pero no interrumpe el resto del reporte).
    """

    # Tamano "ancho" pensado para pagina apaisada: ocupa casi todo el
    # ancho util de una hoja landscape.
    FIGSIZE_ANCHO = (12.5, 6.0)
    FIGSIZE_CUADRADO = (8.5, 8.0)

    def __init__(self, temp_dir: str, cfg: Optional[ConfigReporte] = None):
        self.temp_dir = temp_dir
        self.cfg = cfg or ConfigReporte()
        self._contador = 0
        self._setup_matplotlib()

    # -- infraestructura --------------------------------------------------

    def _setup_matplotlib(self) -> None:
        plt.rcParams.update({
            "figure.facecolor": PALETA["fondo_card"],
            "axes.facecolor": PALETA["fondo_card"],
            "text.color": "white",
            "axes.labelcolor": "white",
            "xtick.color": PALETA["texto_secundario"],
            "ytick.color": PALETA["texto_secundario"],
            "font.size": 10,
        })

    def _archivo(self, sufijo: str) -> str:
        self._contador += 1
        return os.path.join(self.temp_dir, f"grafico_{self._contador:03d}{sufijo}.png")

    def _nueva_figura(self, figsize: Tuple[float, float]):
        fig, ax = plt.subplots(figsize=figsize, dpi=self.cfg.dpi)
        fig.patch.set_facecolor(PALETA["fondo_card"])
        return fig, ax

    def _estilo_base(self, ax, titulo: str = "") -> None:
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color("#475569")
        ax.tick_params(colors=PALETA["texto_secundario"], labelsize=9)
        if titulo:
            ax.set_title(titulo, fontsize=15, fontweight="bold", color="white", pad=16)
        ax.yaxis.grid(True, linestyle="--", alpha=0.2, color="white")
        ax.set_axisbelow(True)

    def _guardar(self, fig, sufijo: str) -> Optional[str]:
        """Guarda y cierra SIEMPRE la figura (evita fugas de memoria),
        y captura cualquier error de renderizado sin tumbar el reporte."""
        ruta = self._archivo(sufijo)
        try:
            fig.tight_layout()
            fig.savefig(ruta, dpi=self.cfg.dpi, bbox_inches="tight",
                        facecolor=PALETA["fondo_card"])
            return ruta
        except Exception:
            logger.error("Error guardando grafico '%s':\n%s", sufijo, traceback.format_exc())
            return None
        finally:
            plt.close(fig)

    @staticmethod
    def _con_manejo_errores(
        func: Callable[..., Optional[str]],
    ) -> Callable[..., Optional[str]]:
        """Decorador: si el calculo del grafico falla, se loguea y se
        devuelve None en vez de romper todo el PDF."""
        @wraps(func)
        def wrapper(
            self: "GraficoGenerator",
            data: Dict[str, float],
            titulo: str = "",
            *args: Any,
            **kwargs: Any,
        ) -> Optional[str]:
            if not data:
                return None
            try:
                return func(self, data, titulo, *args, **kwargs)
            except Exception:
                logger.error("Error generando grafico '%s':\n%s", titulo, traceback.format_exc())
                return None

        return wrapper

    # -- graficos -----------------------------------------------------------

    @_con_manejo_errores
    def pastel(self, data: Dict[str, float], titulo: str = "") -> Optional[str]:
        labels, values, total_general = _top_items(data, 8)
        total_mostrado = sum(values)
        fig, ax = self._nueva_figura(self.FIGSIZE_CUADRADO)
        colores = COLORES_GRAFICOS[: len(labels)]

        wedges, _, _ = ax.pie(
            values, labels=None, autopct="%1.1f%%", startangle=90, colors=colores,
            pctdistance=0.75, wedgeprops=dict(width=0.5, edgecolor="white", linewidth=2),
            textprops=dict(color="white", fontsize=10, fontweight="bold"),
        )

        centro = matplotlib.patches.Circle((0, 0), 0.45, fc=PALETA["fondo_card"])
        ax.add_artist(centro)
        ax.text(0, 0.05, f"{total_mostrado:,.0f}", ha="center", va="center",
                fontsize=19, fontweight="bold", color="white")
        ax.text(0, -0.15, "TOTAL MOSTRADO", ha="center", va="center",
                fontsize=9, color=PALETA["texto_secundario"])

        leyenda = [f"{l} ({v:,.0f} · {_pct(v, total_general):.1f}%)" for l, v in zip(labels, values)]
        ax.legend(wedges, leyenda, title="Items", loc="center left",
                   bbox_to_anchor=(1.02, 0, 0.6, 1), fontsize=10, title_fontsize=11,
                   frameon=False, labelcolor="white")
        ax.set_title(titulo, fontsize=17, fontweight="bold", color="white", pad=20)
        return self._guardar(fig, "_pastel")

    @_con_manejo_errores
    def barras_verticales(self, data: Dict[str, float], titulo: str = "") -> Optional[str]:
        labels, values, total_general = _top_items(data, 12)
        fig, ax = self._nueva_figura(self.FIGSIZE_ANCHO)
        self._estilo_base(ax, titulo)

        x = np.arange(len(labels))
        colores = COLORES_GRAFICOS[: len(labels)]
        bars = ax.bar(x, values, color=colores, edgecolor="white", linewidth=0.8, alpha=0.92, width=0.62)

        maximo = max(values) if values else 1
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + maximo * 0.015,
                     f"{val:,.0f}\n({_pct(val, total_general):.1f}%)", ha="center", va="bottom",
                     fontsize=8, color="white", fontweight="bold")

        ax.set_xticks(x)
        ax.set_xticklabels([_envolver_etiqueta(l) for l in labels], rotation=0, ha="center", fontsize=9)
        ax.margins(y=0.18)
        return self._guardar(fig, "_barras_v")

    @_con_manejo_errores
    def barras_horizontales(self, data: Dict[str, float], titulo: str = "") -> Optional[str]:
        labels, values, total_general = _top_items(data, 12)
        fig, ax = self._nueva_figura(self.FIGSIZE_ANCHO)
        self._estilo_base(ax, titulo)

        y = np.arange(len(labels))
        colores = COLORES_GRAFICOS[: len(labels)]
        bars = ax.barh(y, values, color=colores, edgecolor="white", linewidth=0.8, alpha=0.92, height=0.62)

        maximo = max(values) if values else 1
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + maximo * 0.01, bar.get_y() + bar.get_height() / 2,
                     f" {val:,.0f} ({_pct(val, total_general):.1f}%)", ha="left", va="center",
                     fontsize=9, color="white", fontweight="bold")

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=10)
        ax.invert_yaxis()
        ax.margins(x=0.18)
        return self._guardar(fig, "_barras_h")

    @_con_manejo_errores
    def lineas(self, data: Dict[str, float], titulo: str = "") -> Optional[str]:
        labels = list(data.keys())[:14]
        values = [float(data[k]) for k in labels]
        total_general = sum(float(v) for v in data.values())
        fig, ax = self._nueva_figura(self.FIGSIZE_ANCHO)
        self._estilo_base(ax, titulo)

        x = np.arange(len(labels))
        ax.plot(x, values, "o-", linewidth=2.6, color=PALETA["acento"], markersize=7,
                 markerfacecolor=PALETA["acento"], markeredgecolor="white", markeredgewidth=1.5)
        ax.fill_between(x, values, alpha=0.15, color=PALETA["acento"])
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)

        for xi, yi in zip(x, values):
            ax.annotate(f"{yi:,.0f}\n({_pct(yi, total_general):.1f}%)", (xi, yi),
                        textcoords="offset points", xytext=(0, 12), ha="center",
                        fontsize=7.5, color="white", fontweight="bold")
        ax.margins(y=0.2)
        return self._guardar(fig, "_lineas")

    @_con_manejo_errores
    def area(self, data: Dict[str, float], titulo: str = "") -> Optional[str]:
        labels = list(data.keys())[:12]
        values = [float(data[k]) for k in labels]
        fig, ax = self._nueva_figura(self.FIGSIZE_ANCHO)
        self._estilo_base(ax, titulo)

        x = np.arange(len(labels))
        ax.fill_between(x, 0, values, alpha=0.6, color=PALETA["acento"])
        ax.fill_between(x, 0, [v * 0.7 for v in values], alpha=0.4, color=PALETA["info"])
        ax.plot(x, values, "o-", linewidth=2, color="white", markersize=5)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)

        maximo = max(values) if values else 1
        for xi, yi in zip(x, values):
            ax.text(float(xi), yi + maximo * 0.03, f"{yi:,.0f}", ha="center",
                     fontsize=8, color="white", fontweight="bold")
        ax.margins(y=0.15)
        return self._guardar(fig, "_area")

    @_con_manejo_errores
    def radar(self, data: Dict[str, float], titulo: str = "") -> Optional[str]:
        labels, values, _ = _top_items(data, 8)
        maximo = max(values) if values else 1
        valores_norm = [v / maximo * 100 for v in values]
        valores_norm += valores_norm[:1]
        angulos = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        angulos += angulos[:1]

        fig, ax = plt.subplots(figsize=(8.5, 8), subplot_kw=dict(projection="polar"), dpi=self.cfg.dpi)
        fig.patch.set_facecolor(PALETA["fondo_card"])
        ax.plot(angulos, valores_norm, "o-", linewidth=2.2, color=PALETA["acento"],
                 markersize=8, markerfacecolor=PALETA["acento"])
        ax.fill(angulos, valores_norm, alpha=0.25, color=PALETA["acento"])
        ax.set_xticks(angulos[:-1])
        ax.set_xticklabels([_envolver_etiqueta(l, 12) for l in labels], fontsize=9, color="white")
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25%", "50%", "75%", "100%"], color=PALETA["texto_secundario"], fontsize=8)
        ax.set_facecolor(PALETA["fondo_card"])
        ax.grid(True, alpha=0.3, color="white")
        ax.spines["polar"].set_color("#475569")
        ax.set_title(titulo, fontsize=15, fontweight="bold", color="white", pad=22)
        return self._guardar(fig, "_radar")

    @_con_manejo_errores
    def piramide(self, data: Dict[str, float], titulo: str = "") -> Optional[str]:
        labels, values, total_general = _top_items(data, 8)
        fig, ax = self._nueva_figura(self.FIGSIZE_ANCHO)
        self._estilo_base(ax, titulo)
        maximo = max(values)

        for i, (label, val) in enumerate(zip(labels, values)):
            width = (val / maximo) * 0.92
            left = (1 - width) / 2
            color = COLORES_GRAFICOS[i % len(COLORES_GRAFICOS)]
            ax.barh(i, width, left=left, height=0.72, color=color, alpha=0.88,
                     edgecolor="white", linewidth=1)
            ax.text(0.5, i, f"{label}: {val:,.0f} ({_pct(val, total_general):.1f}%)",
                     ha="center", va="center", fontsize=10.5, fontweight="bold", color="white")

        ax.set_yticks([])
        ax.set_xticks([])
        ax.set_xlim(0, 1)
        ax.invert_yaxis()
        for spine in ax.spines.values():
            spine.set_visible(False)
        return self._guardar(fig, "_piramide")

    @_con_manejo_errores
    def heatmap(self, data: Dict[str, float], titulo: str = "") -> Optional[str]:
        labels, values, total_general = _top_items(data, 16)
        fig, ax = plt.subplots(figsize=self.FIGSIZE_ANCHO, dpi=self.cfg.dpi)
        fig.patch.set_facecolor(PALETA["fondo_card"])
        ax.set_facecolor(PALETA["fondo_card"])

        maximo = max(values) if values else 1
        n_cols = 5
        n_filas = (len(labels) + n_cols - 1) // n_cols

        for i, (label, val) in enumerate(zip(labels, values)):
            fila, col = divmod(i, n_cols)
            color = plt.cm.viridis(val / maximo)
            ax.add_patch(matplotlib.patches.Rectangle(
                (col, n_filas - 1 - fila), 0.95, 0.95,
                facecolor=color, edgecolor="white", linewidth=2, alpha=0.9))
            ax.text(col + 0.475, n_filas - 1 - fila + 0.62, label[:14],
                     ha="center", va="center", fontsize=9, color="white", fontweight="bold")
            ax.text(col + 0.475, n_filas - 1 - fila + 0.38, f"{val:,.0f}",
                     ha="center", va="center", fontsize=9, color="white", fontweight="bold")
            ax.text(col + 0.475, n_filas - 1 - fila + 0.16, f"({_pct(val, total_general):.1f}%)",
                     ha="center", va="center", fontsize=7.5, color="white", alpha=0.85)

        ax.set_xlim(-0.1, n_cols)
        ax.set_ylim(-0.1, n_filas)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(titulo, fontsize=15, fontweight="bold", color="white", pad=16)
        for spine in ax.spines.values():
            spine.set_visible(False)
        return self._guardar(fig, "_heatmap")

    @_con_manejo_errores
    def comparativo(self, data: Dict[str, float], titulo: str = "") -> Optional[str]:
        labels = list(data.keys())[:10]
        values = [float(data[k]) for k in labels]
        rng = np.random.default_rng(42)
        metas = [v * rng.uniform(0.8, 1.3) for v in values]

        fig, ax = self._nueva_figura(self.FIGSIZE_ANCHO)
        self._estilo_base(ax, titulo)
        x = np.arange(len(labels))
        ancho = 0.36

        b1 = ax.bar(x - ancho / 2, values, ancho, label="Real", color=PALETA["acento"],
                     alpha=0.92, edgecolor="white")
        b2 = ax.bar(x + ancho / 2, metas, ancho, label="Meta", color=PALETA["exito"],
                     alpha=0.92, edgecolor="white")
        ax.set_xticks(x)
        ax.set_xticklabels([_envolver_etiqueta(l) for l in labels], fontsize=9)
        ax.legend(loc="upper right", facecolor=PALETA["fondo_card"], edgecolor="#475569",
                   labelcolor="white", fontsize=10)

        maximo = max(max(values), max(metas))
        for barras in (b1, b2):
            for bar in barras:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + maximo * 0.012,
                         f"{bar.get_height():,.0f}", ha="center", va="bottom",
                         fontsize=7.5, color="white", fontweight="bold")
        ax.margins(y=0.15)
        return self._guardar(fig, "_comparativo")

    @_con_manejo_errores
    def treemap(self, data: Dict[str, float], titulo: str = "") -> Optional[str]:
        labels, values, total_general = _top_items(data, 14)
        total_mostrado = sum(values)
        fig, ax = plt.subplots(figsize=self.FIGSIZE_ANCHO, dpi=self.cfg.dpi)
        fig.patch.set_facecolor(PALETA["fondo_card"])
        ax.set_facecolor(PALETA["fondo_card"])

        max_w, max_h = 14.0, 7.0
        x = y = 0.0
        fila_alto_max = 0.0
        for i, (label, val) in enumerate(zip(labels, values)):
            area = (val / total_mostrado) * (max_w * max_h)
            w = min(np.sqrt(area * 1.6), max_w)
            h = area / w if w else 0
            if x + w > max_w:
                x = 0.0
                y += fila_alto_max + 0.12
                fila_alto_max = 0.0
            color = COLORES_GRAFICOS[i % len(COLORES_GRAFICOS)]
            ax.add_patch(matplotlib.patches.Rectangle((x, y), w, h, facecolor=color,
                                                        alpha=0.87, edgecolor="white", linewidth=2))
            fontsize = min(11, max(7, w * 1.1))
            ax.text(x + w / 2, y + h / 2, f"{label}\n{val:,.0f}\n({_pct(val, total_general):.1f}%)",
                     ha="center", va="center", fontsize=fontsize, color="white", fontweight="bold")
            x += w + 0.12
            fila_alto_max = max(fila_alto_max, h)

        ax.set_xlim(0, max_w)
        ax.set_ylim(0, y + fila_alto_max + 0.2)
        ax.invert_yaxis()
        ax.axis("off")
        ax.set_title(titulo, fontsize=15, fontweight="bold", color="white", pad=16)
        return self._guardar(fig, "_treemap")

    def kpis_resumen(self, kpis: Dict[str, float]) -> Optional[str]:
        etiquetas = ["Ventas", "Tickets", "Registros", "Clientes", "Productos"]
        valores = [
            float(kpis.get("ventas_totales", 0)),
            float(kpis.get("tickets_totales", 0)),
            float(kpis.get("registros", 0)),
            float(kpis.get("clientes_totales", 0)),
            float(kpis.get("productos_vendidos", 0)),
        ]
        colores = [PALETA["acento"], PALETA["exito"], PALETA["alerta"], PALETA["morado"], PALETA["rosa"]]

        fig, ax = self._nueva_figura(self.FIGSIZE_ANCHO)
        self._estilo_base(ax, "KPIs Empresariales — Resumen")
        y = np.arange(len(etiquetas))
        bars = ax.barh(y, valores, color=colores, edgecolor="white", linewidth=1, alpha=0.92, height=0.6)

        maximo = max(valores) if valores else 1
        for bar, val in zip(bars, valores):
            ax.text(bar.get_width() + maximo * 0.01, bar.get_y() + bar.get_height() / 2,
                     f" {val:,.0f}", ha="left", va="center", fontsize=12, color="white", fontweight="bold")

        ax.set_yticks(y)
        ax.set_yticklabels(etiquetas, fontsize=12, fontweight="bold")
        ax.invert_yaxis()
        ax.margins(x=0.18)
        return self._guardar(fig, "_kpis")


# =============================================================================
# CANVAS CON NUMERACION DE PAGINAS ("Pagina X de Y")
# =============================================================================

class _CanvasNumerado(pdf_canvas.Canvas):
    """Canvas que dibuja encabezado y pie en cada pagina, incluyendo el
    total de paginas (que solo se conoce al terminar de construir el
    documento), tal como hace Word/Power BI en sus exportaciones."""

    def __init__(self, *args, cfg: ConfigReporte, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas: List[Dict[str, Any]] = []
        self.cfg = cfg

    def showPage(self) -> None:
        self._paginas.append(dict(self.__dict__))
        # ReportLab expone este método en tiempo de ejecución, pero no en
        # todos sus archivos de tipos estáticos.
        cast(Any, self)._startPage()

    def save(self) -> None:
        total = len(self._paginas)
        for i, estado in enumerate(self._paginas, start=1):
            self.__dict__.update(estado)
            self._dibujar_pie(i, total)
            super().showPage()
        super().save()

    def _dibujar_pie(self, pagina: int, total: int) -> None:
        ancho, _ = self.cfg.pagesize
        m = self.cfg.margen
        self.setStrokeColor(HexColor(PALETA["borde"]))
        self.setLineWidth(0.6)
        self.line(m, m * 0.7, ancho - m, m * 0.7)
        self.setFont("Helvetica", 8)
        self.setFillColor(HexColor(PALETA["texto_secundario"]))
        self.drawString(m, m * 0.4, self.cfg.titulo_empresa)
        self.drawRightString(ancho - m, m * 0.4, f"Página {pagina} de {total}")


# =============================================================================
# GENERADOR DE PDF
# =============================================================================

class PDFReportGenerator:
    """Construye el reporte PDF completo: portada, tabla + grafico de
    KPIs y una seccion por cada item de `analisis`, todo dimensionado
    dinamicamente en funcion del ancho de pagina configurado."""

    def __init__(self, filename: str = "reporte_powerbi.pdf",
                 cfg: Optional[ConfigReporte] = None):
        self.filename = filename
        self.cfg = cfg or ConfigReporte()
        self._setup_styles()

    # -- estilos ------------------------------------------------------------

    def _setup_styles(self) -> None:
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name="DashboardTitle", parent=self.styles["Title"], fontSize=26,
            textColor=HexColor(PALETA["acento"]), spaceAfter=12,
            alignment=TA_CENTER, fontName="Helvetica-Bold"))
        self.styles.add(ParagraphStyle(
            name="DashboardSubtitle", parent=self.styles["Normal"], fontSize=12,
            textColor=HexColor(PALETA["texto_secundario"]), alignment=TA_CENTER, spaceAfter=20))
        self.styles.add(ParagraphStyle(
            name="SectionHeader", parent=self.styles["Heading2"], fontSize=15,
            textColor=HexColor(PALETA["acento"]), spaceBefore=14, spaceAfter=10,
            borderWidth=1, borderColor=HexColor(PALETA["acento"]), borderPadding=6))
        # Estilos para texto DENTRO de celdas de tabla (permiten wrap)
        self.styles.add(ParagraphStyle(
            name="CeldaHeader", parent=self.styles["Normal"], fontSize=10,
            textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=12))
        self.styles.add(ParagraphStyle(
            name="CeldaTexto", parent=self.styles["Normal"], fontSize=9.5,
            textColor=colors.white, fontName="Helvetica", alignment=TA_LEFT, leading=12))
        self.styles.add(ParagraphStyle(
            name="CeldaNumero", parent=self.styles["Normal"], fontSize=9.5,
            textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_RIGHT, leading=12))
        self.styles.add(ParagraphStyle(
            name="CeldaCentro", parent=self.styles["Normal"], fontSize=9.5,
            textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=12))

    # -- tablas ---------------------------------------------------------------

    def _p(self, texto: str, estilo: str) -> rl.Paragraph:
        return rl.Paragraph(str(texto), self.styles[estilo])

    def _crear_tabla_kpis(self, kpis: Dict[str, float]) -> rl.Table:
        """Tabla de KPIs; los anchos de columna son proporcionales al
        ancho util de la pagina, asi que se ve bien tanto en A4 como en
        landscape."""
        filas_datos = [
            ("Ventas Totales", f"S/ {kpis.get('ventas_totales', 0):,.2f}"),
            ("Tickets Procesados", f"{kpis.get('tickets_totales', 0):,}"),
            ("Registros", f"{kpis.get('registros', 0):,}"),
            ("Clientes Únicos", f"{kpis.get('clientes_totales', 0):,}"),
            ("Productos Vendidos", f"{kpis.get('productos_vendidos', 0):,}"),
            ("Ticket Promedio", f"S/ {kpis.get('ticket_promedio', 0):,.2f}"),
            ("Tasa de Conversión", f"{kpis.get('conversion', 0):.1f}%"),
            ("Crecimiento", f"{kpis.get('crecimiento', 0):+.1f}%"),
        ]
        datos = [[self._p("INDICADOR", "CeldaHeader"), self._p("VALOR", "CeldaHeader")]]
        datos += [[self._p(k, "CeldaTexto"), self._p(v, "CeldaNumero")] for k, v in filas_datos]

        ancho_total = self.cfg.ancho_util
        col_widths = [ancho_total * 0.62, ancho_total * 0.38]

        tabla = rl.Table(datos, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(rl.TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(PALETA["acento"])),
            ("LINEBELOW", (0, 0), (-1, 0), 2, HexColor(PALETA["acento"])),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor(PALETA["fondo_card"]), HexColor("#243349")]),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor(PALETA["borde"])),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        return tabla

    def _crear_tabla_resumen(self, data: Dict[str, float], n: int = 8) -> rl.Table:
        """Top-N con rango, valor y % — anchos proporcionales al ancho
        de pagina y celdas en Paragraph para que los nombres largos
        hagan salto de linea en vez de truncarse."""
        labels, values, total_general = _top_items(data, n)

        datos = [[self._p("RANK", "CeldaHeader"), self._p("ITEM", "CeldaHeader"),
                  self._p("VALOR", "CeldaHeader"), self._p("% DEL TOTAL", "CeldaHeader")]]
        for i, (label, val) in enumerate(zip(labels, values)):
            rank = MEDALLAS[i] if i < len(MEDALLAS) else f"{i + 1}°"
            datos.append([
                self._p(rank, "CeldaCentro"),
                self._p(label, "CeldaTexto"),
                self._p(f"{val:,.0f}", "CeldaNumero"),
                self._p(f"{_pct(val, total_general):.1f}%", "CeldaNumero"),
            ])
        datos.append([
            self._p("", "CeldaCentro"), self._p("TOTAL (top mostrado)", "CeldaHeader"),
            self._p(f"{sum(values):,.0f}", "CeldaNumero"),
            self._p(f"{_pct(sum(values), total_general):.1f}%", "CeldaNumero"),
        ])

        ancho_total = self.cfg.ancho_util
        col_widths = [ancho_total * 0.08, ancho_total * 0.52, ancho_total * 0.20, ancho_total * 0.20]

        tabla = rl.Table(datos, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(rl.TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(PALETA["acento"])),
            ("LINEBELOW", (0, 0), (-1, 0), 2, HexColor(PALETA["acento"])),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [HexColor(PALETA["fondo_card"]), HexColor("#243349")]),
            ("BACKGROUND", (0, -1), (-1, -1), HexColor(PALETA["exito"])),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor(PALETA["borde"])),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        return tabla

    # -- imagenes ---------------------------------------------------------------

    def _imagen_flowable(
        self,
        ruta: Optional[str],
        alto_max_cm: float = 11.5,
    ) -> Optional[rl.Image]:
        """Crea un Flowable Image respetando la relacion de aspecto y
        ocupando el maximo ancho util posible (grafico "amplio")."""
        if ruta is None or not os.path.exists(ruta):
            return None
        ancho, alto = _tamano_imagen_proporcional(ruta, self.cfg.ancho_util, alto_max_cm * cm)
        return rl.Image(ruta, width=ancho, height=alto)

    # -- construccion del documento ---------------------------------------------

    def generar(self, resultado: Dict) -> bool:
        """Punto de entrada principal. Devuelve True/False segun si el
        PDF se genero correctamente; nunca lanza excepcion hacia afuera."""
        kpis = resultado.get("kpis", {})
        analisis = resultado.get("analisis", [])

        try:
            with tempfile.TemporaryDirectory(prefix="dashboard_pdf_") as temp_dir:
                graficos = GraficoGenerator(temp_dir, self.cfg)
                contenido = self._construir_contenido(kpis, analisis, graficos)

                doc = rl.SimpleDocTemplate(
                    self.filename,
                    pagesize=self.cfg.pagesize,
                    rightMargin=self.cfg.margen, leftMargin=self.cfg.margen,
                    topMargin=self.cfg.margen, bottomMargin=self.cfg.margen * 1.4,
                    title=self.cfg.subtitulo_reporte,
                )
                doc.build(
                    contenido,
                    canvasmaker=lambda *a, **kw: _CanvasNumerado(*a, cfg=self.cfg, **kw),
                )

            logger.info("PDF generado correctamente: %s", self.filename)
            return True

        except Exception:
            logger.error("Error generando PDF:\n%s", traceback.format_exc())
            return False

    def _construir_contenido(self, kpis: Dict, analisis: List[Dict],
                              graficos: GraficoGenerator) -> List:
        contenido: List = []

        # ---------- Portada ----------
        contenido.append(rl.Spacer(1, 2.2 * cm))
        contenido.append(rl.Paragraph(self.cfg.subtitulo_reporte.upper(), self.styles["DashboardTitle"]))
        contenido.append(rl.Paragraph(self.cfg.titulo_empresa, self.styles["DashboardSubtitle"]))
        fecha = datetime.now().strftime("%d de %B de %Y — %H:%M hrs")
        contenido.append(rl.Paragraph(f"Generado: {fecha}", self.styles["DashboardSubtitle"]))
        contenido.append(rl.Spacer(1, 1 * cm))
        contenido.append(rl.HRFlowable(width="100%", thickness=2, color=HexColor(PALETA["acento"])))
        contenido.append(rl.PageBreak())

        # ---------- KPIs ----------
        contenido.append(rl.Paragraph("INDICADORES CLAVE (KPIs)", self.styles["SectionHeader"]))
        contenido.append(rl.Spacer(1, 8))
        contenido.append(self._crear_tabla_kpis(kpis))
        contenido.append(rl.Spacer(1, 16))

        img_kpi = graficos.kpis_resumen(kpis)
        flow_kpi = self._imagen_flowable(img_kpi, alto_max_cm=9.5)
        if flow_kpi:
            contenido.append(flow_kpi)
        contenido.append(rl.PageBreak())

        # ---------- Analisis por categoria ----------
        contenido.append(rl.Paragraph("ANÁLISIS DETALLADO POR CATEGORÍA", self.styles["SectionHeader"]))
        contenido.append(rl.Spacer(1, 10))

        tipos_graficos: Sequence[Callable] = (
            graficos.pastel, graficos.barras_verticales, graficos.barras_horizontales,
            graficos.lineas, graficos.area, graficos.radar, graficos.piramide,
            graficos.heatmap, graficos.comparativo, graficos.treemap,
        )

        secciones_validas = 0
        for idx, item in enumerate(analisis):
            top = item.get("top")
            if not isinstance(top, dict) or not top:
                continue

            nombre = item.get("columna", f"Grupo {idx + 1}")
            contenido.append(rl.Paragraph(nombre, self.styles["Heading2"]))
            contenido.append(rl.Spacer(1, 6))
            contenido.append(self._crear_tabla_resumen(top))
            contenido.append(rl.Spacer(1, 14))

            grafico_func = tipos_graficos[idx % len(tipos_graficos)]
            ruta_img = grafico_func(top, nombre)
            flow_img = self._imagen_flowable(ruta_img, alto_max_cm=10.5)
            if flow_img:
                contenido.append(flow_img)
            else:
                contenido.append(rl.Paragraph(
                    "No se pudo generar el gráfico para esta categoría.", self.styles["DashboardSubtitle"]))

            contenido.append(rl.Spacer(1, 18))
            secciones_validas += 1
            if secciones_validas % 1 == 0 and idx < len(analisis) - 1:
                contenido.append(rl.PageBreak())

        # ---------- Pie de reporte ----------
        contenido.append(rl.Spacer(1, 10))
        contenido.append(rl.HRFlowable(width="100%", thickness=1, color=HexColor(PALETA["borde"])))
        contenido.append(rl.Spacer(1, 8))
        contenido.append(rl.Paragraph(
            f"{self.cfg.titulo_empresa} · Generado automáticamente", self.styles["Italic"]))
        contenido.append(rl.Paragraph(
            f"Categorías analizadas: {secciones_validas} · Registros totales: {kpis.get('registros', 0):,}",
            self.styles["DashboardSubtitle"]))

        return contenido


# =============================================================================
# FUNCION DE COMPATIBILIDAD CON EL CODIGO ANTERIOR
# =============================================================================

def exportar_pdf(resultado: Dict, archivo: str = "reporte_powerbi.pdf",
                  orientacion: str = "landscape") -> bool:
    """Mantiene la misma firma que la version anterior para no romper
    el resto del proyecto que ya llama a `exportar_pdf(...)`."""
    cfg = ConfigReporte(orientacion=orientacion)
    generador = PDFReportGenerator(archivo, cfg)
    return generador.generar(resultado)


# =============================================================================
# PRUEBA MANUAL
# =============================================================================

if __name__ == "__main__":
    datos_prueba = {
        "kpis": {
            "ventas_totales": 154320.50, "tickets_totales": 3421, "registros": 15000,
            "clientes_totales": 892, "productos_vendidos": 5234, "ticket_promedio": 45.11,
            "conversion": 68.5, "crecimiento": 23.4,
        },
        "analisis": [
            {"columna": "Productos Top", "top": {"Laptop Lenovo ThinkPad": 45000, "iPhone 15 Pro": 38000,
                                                    "Monitor LG UltraWide": 22000, "Teclado Mecánico": 15000,
                                                    "Mouse Inalámbrico": 12000, "Auriculares Bluetooth": 9000}},
            {"columna": "Ciudades", "top": {"Madrid": 52000, "Barcelona": 41000, "Valencia": 28000,
                                             "Sevilla": 19000, "Bilbao": 14000, "Málaga": 9000}},
            {"columna": "Vendedores", "top": {"Carlos": 35000, "Ana": 32000, "Luis": 28000,
                                               "María": 24000, "Pedro": 19000}},
            {"columna": "Categorías", "top": {"Electrónica": 85000, "Hogar": 42000, "Deportes": 18000,
                                               "Jardín": 12000, "Libros": 9000}},
            {"columna": "Meses", "top": {"Enero": 12000, "Febrero": 15000, "Marzo": 18000,
                                          "Abril": 22000, "Mayo": 28000, "Junio": 31000}},
        ],
    }
    exportar_pdf(datos_prueba, "prueba_reporte.pdf", orientacion="landscape")