from tokenize import PlainToken

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QGridLayout, QFrame, QHBoxLayout,
    QPushButton, QMessageBox, QComboBox, QSizePolicy,
    QApplication, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QTabWidget,
    QFileDialog, QSplitter, QStackedWidget
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import json
import csv
from datetime import datetime
from collections import OrderedDict
import random


# =============================================================================
# 🎨 PALETA DE COLORES PROFESIONAL
# =============================================================================

PALETA = {
    "fondo": "#0f172a",
    "fondo_card": "#1e293b",
    "fondo_hover": "#334155",
    "borde": "#475569",
    "texto_principal": "#f8fafc",
    "texto_secundario": "#94a3b8",
    "acento": "#3b82f6",
    "acento_hover": "#2563eb",
    "exito": "#10b981",
    "alerta": "#f59e0b",
    "peligro": "#ef4444",
    "info": "#06b6d4",
    "morado": "#8b5cf6",
    "rosa": "#ec4899",
    "lima": "#84cc16",
    "naranja": "#f97316",
}

COLORES_GRAFICOS = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#64748b',
    '#a855f7', '#14b8a6', '#f43f5e', '#22c55e', '#eab308',
    '#6366f1', '#0ea5e9', '#f472b6', '#a3e635', '#fb923c'
]


# =============================================================================
# 🛠️ FUNCIONES AUXILIARES DE ESTILO
# =============================================================================

def aplicar_estilo_base(fig, ax, titulo=""):
    """Aplica estilo oscuro profesional a cualquier grafico."""
    fig.patch.set_facecolor(PALETA['fondo_card'])
    ax.set_facecolor(PALETA['fondo_card'])

    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color(PALETA['borde'])

    ax.tick_params(colors=PALETA['texto_secundario'], labelsize=9)
    if titulo:
        ax.set_title(titulo, fontsize=14, fontweight='bold', 
                    color=PALETA['texto_principal'], pad=15)
    ax.yaxis.grid(True, linestyle='--', alpha=0.2, color='white')
    ax.set_axisbelow(True)


def crear_figura_vacia(mensaje="Sin datos disponibles"):
    """Crea figura vacia con mensaje profesional."""
    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.text(0.5, 0.5, mensaje, ha='center', va='center', 
           fontsize=14, color=PALETA['texto_secundario'], fontweight='bold')
    fig.patch.set_facecolor(PALETA['fondo_card'])
    ax.set_facecolor(PALETA['fondo_card'])
    ax.axis('off')
    return fig


# =============================================================================
# 1 - BARRAS VERTICALES
# =============================================================================

def crear_grafico_barras(data_dict, titulo="", tipo="vertical"):
    """Grafico de barras verticales u horizontales profesional."""
    if not data_dict:
        return crear_figura_vacia()

    ordenado = OrderedDict(sorted(data_dict.items(), key=lambda x: x[1], reverse=True))
    labels = list(ordenado.keys())[:10]
    values = [float(v) for v in list(ordenado.values())[:10]]

    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    aplicar_estilo_base(fig, ax, titulo)

    colores = COLORES_GRAFICOS[:len(labels)]

    if tipo == "horizontal":
        y_pos = np.arange(len(labels))
        bars = ax.barh(y_pos, values, color=colores, 
                      edgecolor='white', linewidth=0.5, alpha=0.9, height=0.6)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=10, color=PALETA['texto_principal'])
        ax.invert_yaxis()
        for bar, val in zip(bars, values):
            ax.text(val + max(values)*0.015, bar.get_y() + bar.get_height()/2.,
                   f'{val:,.0f}', ha='left', va='center', fontsize=9,
                   color='white', fontweight='bold')
    else:
        x_pos = np.arange(len(labels))
        bars = ax.bar(x_pos, values, color=colores, 
                     edgecolor='white', linewidth=0.5, alpha=0.9, width=0.6)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9, 
                          color=PALETA['texto_principal'])
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.015,
                   f'{val:,.0f}', ha='center', va='bottom', fontsize=9,
                   color='white', fontweight='bold')

    fig.subplots_adjust(left=0.15, right=0.95, top=0.88, bottom=0.22)
    return fig


# =============================================================================
# 2 - PASTEL / DONA
# =============================================================================

def crear_grafico_pastel(data_dict, titulo="", tipo="dona"):
    """Grafico circular o de dona profesional."""
    if not data_dict:
        return crear_figura_vacia()

    ordenado = OrderedDict(sorted(data_dict.items(), key=lambda x: x[1], reverse=True))
    labels = list(ordenado.keys())[:8]
    values = [float(v) for v in list(ordenado.values())[:8]]

    fig = Figure(figsize=(5.5, 4.5), dpi=100)
    ax = fig.add_subplot(111)

    colores = COLORES_GRAFICOS[:len(labels)]

    if tipo == "dona":
        wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colores,
                                          autopct='%1.1f%%', startangle=90,
                                          pctdistance=0.75, labeldistance=1.15,
                                          wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2))
        centre_circle = Circle((0, 0), 0.45, fc=PALETA['fondo_card'])
        ax.add_artist(centre_circle)
        total = sum(values)
        ax.text(0, 0, f'{total:,.0f}', ha='center', va='center', 
               fontsize=16, fontweight='bold', color='white')
    else:
        wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colores,
                                          autopct='%1.1f%%', startangle=90,
                                          wedgeprops=dict(edgecolor='white', linewidth=2))

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')

    for text in texts:
        text.set_color(PALETA['texto_secundario'])
        text.set_fontsize(9)

    ax.set_title(titulo, fontsize=14, fontweight='bold', 
                color=PALETA['texto_principal'], pad=15)
    fig.patch.set_facecolor(PALETA['fondo_card'])
    ax.set_facecolor(PALETA['fondo_card'])
    fig.subplots_adjust(left=0.05, right=0.95, top=0.88, bottom=0.05)
    return fig


# =============================================================================
# 3 - LINEAS / TENDENCIA
# =============================================================================

def crear_grafico_lineas(data_dict, titulo=""):
    """Grafico de lineas con area sombreada."""
    if not data_dict:
        return crear_figura_vacia()

    labels = list(data_dict.keys())[:12]
    values = [float(v) for v in [data_dict[k] for k in labels]]

    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    aplicar_estilo_base(fig, ax, titulo)

    x = np.arange(len(labels))
    ax.plot(x, values, 'o-', linewidth=2.5, color=PALETA['acento'], 
           markersize=6, markerfacecolor=PALETA['acento'], markeredgecolor='white', markeredgewidth=1.5)
    ax.fill_between(x, values, alpha=0.15, color=PALETA['acento'])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9)

    for xi, yi in zip(x, values):
        ax.annotate(f'{yi:,.0f}', (xi, yi), textcoords="offset points", 
                   xytext=(0, 12), ha='center', fontsize=8, 
                   color='white', fontweight='bold')

    fig.subplots_adjust(left=0.1, right=0.95, top=0.88, bottom=0.22)
    return fig


# =============================================================================
# 4 - AREA APILADA
# =============================================================================

def crear_grafico_area(data_dict, titulo=""):
    """Grafico de area con gradiente."""
    if not data_dict:
        return crear_figura_vacia()

    labels = list(data_dict.keys())[:10]
    values = [float(v) for v in [data_dict[k] for k in labels]]

    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    aplicar_estilo_base(fig, ax, titulo)

    x = np.arange(len(labels))

    # Crear multiples capas para efecto visual
    ax.fill_between(x, 0, values, alpha=0.6, color=PALETA['acento'])
    ax.fill_between(x, 0, [v*0.7 for v in values], alpha=0.4, color=PALETA['info'])
    ax.plot(x, values, 'o-', linewidth=2, color='white', markersize=5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9)

    for xi, yi in zip(x, values):
        ax.text(float(xi), float(yi + max(values) * 0.03), f'{yi:,.0f}', ha='center', 
               fontsize=8, color='white', fontweight='bold')

    fig.subplots_adjust(left=0.1, right=0.95, top=0.88, bottom=0.22)
    return fig


# =============================================================================
# 5 - RADAR / SPIDER
# =============================================================================

def crear_grafico_radar(data_dict, titulo=""):
    """Grafico de radar/spider con relleno."""
    if not data_dict:
        return crear_figura_vacia()

    ordenado = OrderedDict(sorted(data_dict.items(), key=lambda x: x[1], reverse=True))
    labels = list(ordenado.keys())[:8]
    values = [float(v) for v in list(ordenado.values())[:8]]

    # Normalizar valores
    max_val = max(values) if values else 1
    values_norm = [v / max_val * 100 for v in values]
    values_norm += values_norm[:1]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig = Figure(figsize=(5, 5), dpi=100)
    ax = fig.add_subplot(111, projection='polar')
    fig.patch.set_facecolor(PALETA['fondo_card'])

    ax.plot(angles, values_norm, 'o-', linewidth=2, color=PALETA['acento'], 
            markersize=8, markerfacecolor=PALETA['acento'])
    ax.fill(angles, values_norm, alpha=0.25, color=PALETA['acento'])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9, color=PALETA['texto_principal'])
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], color=PALETA['texto_secundario'], fontsize=8)
    ax.set_facecolor(PALETA['fondo_card'])
    ax.grid(True, alpha=0.3, color='white')
    ax.spines['polar'].set_color(PALETA['borde'])

    ax.set_title(titulo, fontsize=14, fontweight='bold', color=PALETA['texto_principal'], pad=20)
    fig.subplots_adjust(left=0.1, right=0.9, top=0.88, bottom=0.1)
    return fig


# =============================================================================
# 6 - DISPERSION / SCATTER
# =============================================================================

def crear_grafico_scatter(data_dict, titulo=""):
    """Grafico de dispersion con burbujas."""
    if not data_dict:
        return crear_figura_vacia()

    labels = list(data_dict.keys())[:12]
    values = [float(v) for v in [data_dict[k] for k in labels]]

    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    aplicar_estilo_base(fig, ax, titulo)

    x = np.arange(len(labels))
    sizes = [(v / max(values)) * 500 + 50 for v in values]
    colores = COLORES_GRAFICOS[:len(labels)]

    scatter = ax.scatter(x, values, s=sizes, c=colores, alpha=0.7, 
                        edgecolors='white', linewidths=1.5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9)

    for i, (xi, yi, label) in enumerate(zip(x, values, labels)):
        ax.annotate(f'{yi:,.0f}', (xi, yi), textcoords="offset points",
                   xytext=(0, 15), ha='center', fontsize=8, 
                   color='white', fontweight='bold')

    fig.subplots_adjust(left=0.1, right=0.95, top=0.88, bottom=0.22)
    return fig


# =============================================================================
# 7 - PIRAMIDE / FUNNEL
# =============================================================================

def crear_grafico_piramide(data_dict, titulo=""):
    """Grafico de piramide/funnel invertido."""
    if not data_dict:
        return crear_figura_vacia()

    ordenado = OrderedDict(sorted(data_dict.items(), key=lambda x: x[1], reverse=True))
    labels = list(ordenado.keys())[:8]
    values = [float(v) for v in list(ordenado.values())[:8]]

    fig = Figure(figsize=(5.5, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    aplicar_estilo_base(fig, ax, titulo)

    max_val = max(values)
    n = len(labels)

    for i, (label, val) in enumerate(zip(labels, values)):
        width = (val / max_val) * 0.9
        left = (1 - width) / 2
        color = COLORES_GRAFICOS[i % len(COLORES_GRAFICOS)]

        ax.barh(i, width, left=left, height=0.7, color=color, 
               alpha=0.85, edgecolor='white', linewidth=1)

        ax.text(0.5, i, f'{label}: {val:,.0f}', ha='center', va='center',
               fontsize=10, fontweight='bold', color='white')

    ax.set_yticks(range(n))
    ax.set_yticklabels([])
    ax.set_xlim(0, 1)
    ax.invert_yaxis()
    ax.set_xticks([])

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.subplots_adjust(left=0.05, right=0.95, top=0.88, bottom=0.1)
    return fig


# =============================================================================
# 8 - HEATMAP / MAPA DE CALOR
# =============================================================================

def crear_grafico_heatmap(data_dict, titulo=""):
    """Grafico de heatmap con cuadrados de colores."""
    if not data_dict:
        return crear_figura_vacia()

    ordenado = OrderedDict(sorted(data_dict.items(), key=lambda x: x[1], reverse=True))
    labels = list(ordenado.keys())[:16]
    values = [float(v) for v in list(ordenado.values())[:16]]

    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor(PALETA['fondo_card'])
    ax.set_facecolor(PALETA['fondo_card'])

    max_val = max(values) if values else 1
    n_cols = 4
    n_rows = (len(labels) + n_cols - 1) // n_cols

    for i, (label, val) in enumerate(zip(labels, values)):
        row = i // n_cols
        col = i % n_cols

        intensity = val / max_val
        color = plt.cm.viridis(intensity)

        rect = Rectangle((col, n_rows - 1 - row), 0.95, 0.95,
                         facecolor=color, edgecolor='white', linewidth=2, alpha=0.9)
        ax.add_patch(rect)

        ax.text(col + 0.475, n_rows - 1 - row + 0.65, label[:10],
               ha='center', va='center', fontsize=8, color='white',
               fontweight='bold')
        ax.text(col + 0.475, n_rows - 1 - row + 0.35, f'{val:,.0f}',
               ha='center', va='center', fontsize=9, color='white',
               fontweight='bold')

    ax.set_xlim(-0.1, n_cols)
    ax.set_ylim(-0.1, n_rows)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(titulo, fontsize=14, fontweight='bold', 
                color=PALETA['texto_principal'], pad=15)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.subplots_adjust(left=0.05, right=0.95, top=0.88, bottom=0.05)
    return fig


# =============================================================================
# 9 - GAUGE / VELOCIMETRO
# =============================================================================

def crear_grafico_gauge(valor, max_val, titulo="", subtitulo=""):
    """Gauge circular tipo velocimetro."""
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor(PALETA['fondo_card'])
    ax.set_facecolor(PALETA['fondo_card'])

    porcentaje = min(valor / max_val, 1.0)

    # Arco de fondo
    theta = np.linspace(0, np.pi, 100)
    ax.fill_between(np.cos(theta), np.sin(theta), 0, alpha=0.1, color='white')

    # Arco de valor
    theta_val = np.linspace(0, np.pi * porcentaje, 100)
    color = PALETA['exito'] if porcentaje < 0.6 else PALETA['alerta'] if porcentaje < 0.8 else PALETA['peligro']
    ax.fill_between(np.cos(theta_val), np.sin(theta_val), 0, alpha=0.8, color=color)

    # Aguja
    angle = np.pi * porcentaje
    ax.annotate('', xy=(np.cos(angle)*0.85, np.sin(angle)*0.85),
               xytext=(0, 0),
               arrowprops=dict(arrowstyle='->', color='white', lw=3))

    # Centro
    circle = Circle((0, 0), 0.08, color='white')
    ax.add_artist(circle)

    # Textos
    ax.text(0, -0.25, f'{valor:,.0f}', ha='center', va='center',
           fontsize=22, fontweight='bold', color='white')
    ax.text(0, -0.45, subtitulo, ha='center', va='center',
           fontsize=10, color=PALETA['texto_secundario'])

    # Marcas
    for i in range(0, 101, 25):
        angle_mark = np.pi * (i / 100)
        ax.text(np.cos(angle_mark)*0.95, np.sin(angle_mark)*0.95, f'{i}%',
               ha='center', va='center', fontsize=8, color=PALETA['texto_secundario'])

    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.6, 1.2)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(titulo, fontsize=14, fontweight='bold', 
                color=PALETA['texto_principal'], pad=15)

    fig.subplots_adjust(left=0.05, right=0.95, top=0.88, bottom=0.05)
    return fig


# =============================================================================
# 10 - COMPARATIVO DE BARRAS AGRUPADAS
# =============================================================================

def crear_grafico_comparativo(data_dict, titulo=""):
    """Grafico de barras comparativas con multiples series."""
    if not data_dict:
        return crear_figura_vacia()

    labels = list(data_dict.keys())[:8]
    values = [float(v) for v in [data_dict[k] for k in labels]]

    # Crear segunda serie simulada (meta/objetivo)
    metas = [v * random.uniform(0.8, 1.3) for v in values]

    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    aplicar_estilo_base(fig, ax, titulo)

    x = np.arange(len(labels))
    width = 0.35

    bars1 = ax.bar(x - width/2, values, width, label='Real', 
                  color=PALETA['acento'], alpha=0.9, edgecolor='white')
    bars2 = ax.bar(x + width/2, metas, width, label='Meta', 
                  color=PALETA['exito'], alpha=0.9, edgecolor='white')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9)
    ax.legend(loc='upper right', facecolor=PALETA['fondo_card'], 
             edgecolor=PALETA['borde'], labelcolor='white', fontsize=9)

    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(max(values), max(metas))*0.01,
                   f'{height:,.0f}', ha='center', va='bottom', fontsize=7,
                   color='white', fontweight='bold')

    fig.subplots_adjust(left=0.1, right=0.95, top=0.88, bottom=0.22)
    return fig


# =============================================================================
# 11 - HORIZONTAL BARS (TOP RANKING)
# =============================================================================

def crear_grafico_ranking(data_dict, titulo=""):
    """Ranking horizontal con numeros y medallas."""
    if not data_dict:
        return crear_figura_vacia()

    ordenado = OrderedDict(sorted(data_dict.items(), key=lambda x: x[1], reverse=True))
    labels = list(ordenado.keys())[:10]
    values = [float(v) for v in list(ordenado.values())[:10]]

    fig = Figure(figsize=(6, 5), dpi=100)
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor(PALETA['fondo_card'])
    ax.set_facecolor(PALETA['fondo_card'])

    y_pos = np.arange(len(labels))
    colores = COLORES_GRAFICOS[:len(labels)]

    # Fondo de barra
    ax.barh(y_pos, [max(values)]*len(labels), height=0.6, 
           color=PALETA['fondo_hover'], alpha=0.3, edgecolor='none')

    # Barra real
    bars = ax.barh(y_pos, values, height=0.6, color=colores, 
                  alpha=0.9, edgecolor='white', linewidth=0.5)

    # Numeros de ranking
    medallas = ['\U0001f947', '\U0001f948', '\U0001f949', '4.', '5.', '6.', '7.', '8.', '9.', '10.']
    for i, (bar, label, val, medal) in enumerate(zip(bars, labels, values, medallas)):
        ax.text(-max(values)*0.03, bar.get_y() + bar.get_height()/2.,
               medal, ha='right', va='center', fontsize=14)
        ax.text(val + max(values)*0.015, bar.get_y() + bar.get_height()/2.,
               f'{label}: {val:,.0f}', ha='left', va='center', 
               fontsize=9, color='white', fontweight='bold')

    ax.set_yticks([])
    ax.set_xlim(0, max(values) * 1.5)
    ax.invert_yaxis()

    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color(PALETA['borde'])
    ax.tick_params(colors=PALETA['texto_secundario'])
    ax.set_title(titulo, fontsize=14, fontweight='bold', 
                color=PALETA['texto_principal'], pad=15)

    fig.subplots_adjust(left=0.12, right=0.95, top=0.88, bottom=0.1)
    return fig


# =============================================================================
# 12 - TREEMAP (CUADROS ANIDADOS)
# =============================================================================

def crear_grafico_treemap(data_dict, titulo=""):
    """Treemap con cuadros proporcionales."""
    if not data_dict:
        return crear_figura_vacia()

    ordenado = OrderedDict(sorted(data_dict.items(), key=lambda x: x[1], reverse=True))
    labels = list(ordenado.keys())[:12]
    values = [float(v) for v in list(ordenado.values())[:12]]

    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor(PALETA['fondo_card'])
    ax.set_facecolor(PALETA['fondo_card'])

    total = sum(values)
    colores = COLORES_GRAFICOS[:len(labels)]

    # Layout simple de treemap
    x, y = 0, 0
    max_w = 10
    max_h = 8

    for i, (label, val) in enumerate(zip(labels, values)):
        area = (val / total) * (max_w * max_h)
        w = np.sqrt(area * 1.5)
        h = area / w

        if x + w > max_w:
            x = 0
            y += h + 0.1

        rect = Rectangle((x, y), w, h, facecolor=colores[i], 
                            alpha=0.85, edgecolor='white', linewidth=2)
        ax.add_patch(rect)

        fontsize = min(12, max(7, w * 1.5))
        ax.text(x + w/2, y + h/2, f'{label}\\n{val:,.0f}',
               ha='center', va='center', fontsize=fontsize,
               color='white', fontweight='bold')

        x += w + 0.1

    ax.set_xlim(0, max_w)
    ax.set_ylim(0, max_h)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(titulo, fontsize=14, fontweight='bold', 
                color=PALETA['texto_principal'], pad=15)

    fig.subplots_adjust(left=0.05, right=0.95, top=0.88, bottom=0.05)
    return fig


# =============================================================================
# 💎 KPI CARD MEJORADO
# =============================================================================

class KPICard(QFrame):
    def __init__(self, titulo, valor, icono="", color_acento=PALETA['acento'], parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {PALETA['fondo_card']};
                border-radius: 14px;
                border: 1px solid {PALETA['borde']};
            }}
            QFrame:hover {{
                border: 1px solid {color_acento};
            }}
        """)
        self.setMinimumWidth(200)
        self.setMinimumHeight(100)
        self.setMaximumHeight(120)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(18, 16, 18, 16)

        # Fila superior: icono + titulo
        top_layout = QHBoxLayout()

        icono_lbl = QLabel(icono)
        icono_lbl.setStyleSheet(f"color: {color_acento}; font-size: 20px; background: transparent;")
        top_layout.addWidget(icono_lbl)

        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setStyleSheet(f"color: {PALETA['texto_secundario']}; font-size: 11px; background: transparent;")
        self.lbl_titulo.setWordWrap(True)
        top_layout.addWidget(self.lbl_titulo, 1)
        top_layout.addStretch()

        layout.addLayout(top_layout)

        # Valor grande
        valor_str = f"{valor:,.2f}" if isinstance(valor, (int, float)) else str(valor)
        self.lbl_valor = QLabel(valor_str)
        self.lbl_valor.setStyleSheet(f"color: white; font-size: 26px; font-weight: bold; background: transparent;")
        layout.addWidget(self.lbl_valor)

        # Barra decorativa con color
        self.barra = QFrame()
        self.barra.setMaximumHeight(3)
        self.barra.setMinimumHeight(3)
        self.barra.setStyleSheet(f"background-color: {color_acento}; border-radius: 2px;")
        layout.addWidget(self.barra)


# =============================================================================
# 🎛️ SIDEBAR MEJORADO
# =============================================================================

class FilterSidebar(QFrame):
    filtro_cambiado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {PALETA['fondo']};
                border-right: 1px solid {PALETA['borde']};
            }}
            QLabel {{
                color: {PALETA['texto_secundario']};
                font-size: 12px;
                background: transparent;
            }}
        """)
        self.setMaximumWidth(280)
        self.setMinimumWidth(240)

        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(20, 24, 20, 24)

        # Logo / Titulo
        titulo = QLabel("📊 DASHBOARD PRO")
        titulo.setStyleSheet(f"color: white; font-size: 20px; font-weight: bold; background: transparent;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Analisis de Datos Avanzado")
        subtitulo.setStyleSheet(f"color: {PALETA['texto_secundario']}; font-size: 11px; background: transparent;")
        layout.addWidget(subtitulo)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {PALETA['borde']}; max-height: 1px;")
        layout.addWidget(line)

        # Seccion: Filtros
        seccion_filtros = QLabel("🔧 FILTROS")
        seccion_filtros.setStyleSheet(f"color: {PALETA['acento']}; font-size: 10px; font-weight: bold; background: transparent; letter-spacing: 1px;")
        layout.addWidget(seccion_filtros)

        # Columna
        layout.addWidget(QLabel("📊 Columna de Analisis:"))
        self.combo_columna = QComboBox()
        self.combo_columna.setStyleSheet(f"""
            QComboBox {{
                padding: 12px;
                border-radius: 10px;
                background-color: {PALETA['fondo_card']};
                color: white;
                border: 1px solid {PALETA['borde']};
                font-size: 13px;
            }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox QAbstractItemView {{
                background-color: {PALETA['fondo_card']};
                color: white;
                selection-background-color: {PALETA['acento']};
                border: 1px solid {PALETA['borde']};
                border-radius: 8px;
            }}
        """)
        self.combo_columna.currentTextChanged.connect(self.filtro_cambiado.emit)
        layout.addWidget(self.combo_columna)

        # Tipo de grafico
        layout.addWidget(QLabel("📈 Tipo de Visualizacion:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.setStyleSheet(self.combo_columna.styleSheet())
        self.combo_tipo.addItems([
            "Auto (Recomendado)",
            "Barras Verticales",
            "Barras Horizontales", 
            "Pastel / Dona",
            "Lineas / Tendencia",
            "Area / Sombreado",
            "Radar / Spider",
            "Dispersion / Burbujas",
            "Piramide / Funnel",
            "Heatmap / Calor",
            "Gauge / Velocimetro",
            "Comparativo",
            "Ranking Top",
            "Treemap"
        ])
        self.combo_tipo.currentTextChanged.connect(self.filtro_cambiado.emit)
        layout.addWidget(self.combo_tipo)

        # Separador
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet(f"background-color: {PALETA['borde']}; max-height: 1px;")
        layout.addWidget(line2)

        # Seccion: Fechas
        seccion_fechas = QLabel("📅 RANGO DE FECHAS")
        seccion_fechas.setStyleSheet(f"color: {PALETA['acento']}; font-size: 10px; font-weight: bold; background: transparent; letter-spacing: 1px;")
        layout.addWidget(seccion_fechas)

        layout.addWidget(QLabel("Desde:"))
        self.date_inicio = QDateEdit()
        self.date_inicio.setCalendarPopup(True)
        self.date_inicio.setDate(QDate.currentDate().addYears(-1))
        self.date_inicio.setStyleSheet(self.combo_columna.styleSheet())
        self.date_inicio.dateChanged.connect(self.filtro_cambiado.emit)
        layout.addWidget(self.date_inicio)

        layout.addWidget(QLabel("Hasta:"))
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setStyleSheet(self.combo_columna.styleSheet())
        self.date_fin.dateChanged.connect(self.filtro_cambiado.emit)
        layout.addWidget(self.date_fin)

        layout.addStretch()

        # Footer info
        footer = QLabel("v2.0 - Dashboard Pro\\nPowered by PyQt5 + Matplotlib")
        footer.setStyleSheet(f"color: {PALETA['texto_secundario']}; font-size: 9px; background: transparent;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)


# =============================================================================
# 🚀 DASHBOARD PRINCIPAL MEJORADO
# =============================================================================

class Dashboard(QWidget):
    def __init__(self, resultado):
        super().__init__()
        self.resultado = resultado
        self.setWindowTitle("📊 DASHBOARD PRO - Analisis Avanzado")
        self.resize(1600, 950)
        self.setMinimumSize(1300, 750)

        self.setStyleSheet(f"background-color: {PALETA['fondo']};")

        # Layout principal con splitter
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = FilterSidebar()
        self.sidebar.filtro_cambiado.connect(self.actualizar_dashboard)
        main_layout.addWidget(self.sidebar)

        # Contenido principal
        contenido = QWidget()
        contenido.setStyleSheet(f"background-color: {PALETA['fondo']};")
        contenido_layout = QVBoxLayout(contenido)
        contenido_layout.setSpacing(20)
        contenido_layout.setContentsMargins(28, 24, 28, 24)

        # ===== HEADER =====
        header = QHBoxLayout()
        header.setSpacing(16)

        titulo_container = QVBoxLayout()
        titulo = QLabel("📊 DASHBOARD PRO")
        titulo.setStyleSheet(f"color: white; font-size: 28px; font-weight: bold; background: transparent;")
        titulo_container.addWidget(titulo)

        subtitulo = QLabel("Panel de Control Avanzado - Analisis en Tiempo Real")
        subtitulo.setStyleSheet(f"color: {PALETA['texto_secundario']}; font-size: 12px; background: transparent;")
        titulo_container.addWidget(subtitulo)
        header.addLayout(titulo_container)

        header.addStretch()

        # Botones de accion
        btn_export = QPushButton("📄 Exportar PDF")
        btn_export.setStyleSheet(f"""
            QPushButton {{
                background-color: {PALETA['naranja']};
                color: white;
                padding: 12px 24px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #ea580c;
            }}
        """)
        btn_export.clicked.connect(self.exportar_pdf_ui)
        header.addWidget(btn_export)

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {PALETA['acento']};
                color: white;
                padding: 12px 24px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {PALETA['acento_hover']};
            }}
        """)
        btn_refresh.clicked.connect(self.actualizar_dashboard)
        header.addWidget(btn_refresh)

        contenido_layout.addLayout(header)

        # ===== KPIs =====
        self.kpi_scroll = QScrollArea()
        self.kpi_scroll.setWidgetResizable(True)
        self.kpi_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.kpi_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.kpi_scroll.setMaximumHeight(140)
        self.kpi_scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:horizontal {{ background: {PALETA['fondo']}; height: 6px; border-radius: 3px; }}
            QScrollBar::handle:horizontal {{ background: {PALETA['borde']}; border-radius: 3px; }}
        """)
        self.kpi_scroll.setFrameShape(QFrame.NoFrame)

        self.kpi_widget = QWidget()
        self.kpi_widget.setStyleSheet("background: transparent;")
        self.kpi_layout = QHBoxLayout(self.kpi_widget)
        self.kpi_layout.setSpacing(14)
        self.kpi_layout.setContentsMargins(0, 0, 0, 0)
        self.kpi_scroll.setWidget(self.kpi_widget)

        contenido_layout.addWidget(self.kpi_scroll)

        # ===== TABS =====
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {PALETA['borde']};
                border-radius: 14px;
                background-color: {PALETA['fondo_card']};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {PALETA['fondo_card']};
                color: {PALETA['texto_secundario']};
                padding: 14px 28px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-weight: bold;
                font-size: 13px;
                margin-right: 6px;
            }}
            QTabBar::tab:selected {{
                background-color: {PALETA['acento']};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {PALETA['fondo_hover']};
                color: white;
            }}
        """)

        # Tab Graficos
        self.tab_graficos = QWidget()
        self.tab_graficos.setStyleSheet(f"background-color: {PALETA['fondo']};")
        graficos_layout = QVBoxLayout(self.tab_graficos)
        graficos_layout.setContentsMargins(12, 12, 12, 12)

        self.scroll_graficos = QScrollArea()
        self.scroll_graficos.setWidgetResizable(True)
        self.scroll_graficos.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: {PALETA['fondo']}; width: 8px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background: {PALETA['borde']}; border-radius: 4px; min-height: 40px; }}
            QScrollBar::handle:vertical:hover {{ background: {PALETA['acento']}; }}
        """)
        self.scroll_graficos.setFrameShape(QFrame.NoFrame)

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setSpacing(28)
        self.grid.setContentsMargins(12, 12, 12, 12)

        self.scroll_graficos.setWidget(self.grid_widget)
        graficos_layout.addWidget(self.scroll_graficos)

        # Tab Tabla
        self.tab_tabla = QWidget()
        tabla_layout = QVBoxLayout(self.tab_tabla)
        self.tabla = QTableWidget()
        self.tabla.setStyleSheet(f"""
            QTableWidget {{
                background-color: {PALETA['fondo_card']};
                color: white;
                border: 1px solid {PALETA['borde']};
                border-radius: 12px;
                gridline-color: {PALETA['borde']};
                font-size: 13px;
            }}
            QHeaderView::section {{
                background-color: {PALETA['acento']};
                color: white;
                padding: 14px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }}
            QTableWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {PALETA['borde']};
            }}
            QTableWidget::item:selected {{
                background-color: {PALETA['acento']};
            }}
            QTableWidget::item:!selected:nth-child(even) {{
                background-color: {PALETA['fondo_card']};
            }}
        """)
        self.tabla.setAlternatingRowColors(True)
        v_header = self.tabla.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        h_header = self.tabla.horizontalHeader()
        if h_header is not None:
            h_header.setSectionResizeMode(QHeaderView.Stretch)
        tabla_layout.addWidget(self.tabla)

        self.tabs.addTab(self.tab_graficos, "📊 Visualizaciones")
        self.tabs.addTab(self.tab_tabla, "📋 Tabla de Datos")

        contenido_layout.addWidget(self.tabs, 1)

        # Status bar
        self.status = QLabel("✅ Listo - Sistema operativo")
        self.status.setStyleSheet(f"color: {PALETA['texto_secundario']}; font-size: 12px; background: transparent; padding: 6px;")
        contenido_layout.addWidget(self.status)

        main_layout.addWidget(contenido, 1)

        # Inicializar
        self.cargar_filtros()
        self.actualizar_dashboard()

    def cargar_filtros(self):
        self.sidebar.combo_columna.clear()
        self.sidebar.combo_columna.addItem("Todos")
        for item in self.resultado.get("analisis", []):
            if isinstance(item.get("top"), dict):
                self.sidebar.combo_columna.addItem(item.get("columna", ""))

    def seleccionar_tipo_grafico(self, item, tipo_seleccionado, index):
        """Selecciona el tipo de grafico mas apropiado."""
        data = item.get("top", {})
        n_items = len(data)

        if tipo_seleccionado == "Auto (Recomendado)":
            # Logica automatica de seleccion
            tipos_disponibles = [
                ("barras", crear_grafico_barras),
                ("pastel", crear_grafico_pastel),
                ("lineas", crear_grafico_lineas),
                ("area", crear_grafico_area),
                ("radar", crear_grafico_radar),
                ("scatter", crear_grafico_scatter),
                ("piramide", crear_grafico_piramide),
                ("heatmap", crear_grafico_heatmap),
                ("gauge", crear_grafico_gauge),
                ("comparativo", crear_grafico_comparativo),
                ("ranking", crear_grafico_ranking),
                ("treemap", crear_grafico_treemap),
            ]
            return tipos_disponibles[index % len(tipos_disponibles)][1]

        tipo_map = {
            "Barras Verticales": lambda d, t: crear_grafico_barras(d, t, "vertical"),
            "Barras Horizontales": lambda d, t: crear_grafico_barras(d, t, "horizontal"),
            "Pastel / Dona": lambda d, t: crear_grafico_pastel(d, t, "dona"),
            "Lineas / Tendencia": crear_grafico_lineas,
            "Area / Sombreado": crear_grafico_area,
            "Radar / Spider": crear_grafico_radar,
            "Dispersion / Burbujas": crear_grafico_scatter,
            "Piramide / Funnel": crear_grafico_piramide,
            "Heatmap / Calor": crear_grafico_heatmap,
            "Gauge / Velocimetro": lambda d, t: crear_grafico_gauge(sum(d.values()), max(d.values())*1.2, t),
            "Comparativo": crear_grafico_comparativo,
            "Ranking Top": crear_grafico_ranking,
            "Treemap": crear_grafico_treemap,
        }

        return tipo_map.get(tipo_seleccionado, crear_grafico_barras)

    def actualizar_dashboard(self):
        # Limpiar grid
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()

        # Limpiar KPIs
        for i in reversed(range(self.kpi_layout.count())):
            item = self.kpi_layout.itemAt(i)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()

        analisis = self.resultado.get("analisis", [])
        kpis = self.resultado.get("kpis", {})
        filtro = self.sidebar.combo_columna.currentText()
        tipo_grafico = self.sidebar.combo_tipo.currentText()

        # ===== KPIs con iconos y colores =====
        kpi_data = [
            ("💰 Ventas Totales", kpis.get('ventas_totales', 0), PALETA['exito']),
            ("🎟 Tickets", kpis.get('tickets_totales', 0), PALETA['info']),
            ("📁 Registros", kpis.get('registros', 0), PALETA['morado']),
            ("👥 Clientes", kpis.get('clientes_totales', 0), PALETA['acento']),
            ("📦 Productos", kpis.get('productos_vendidos', 0), PALETA['naranja']),
            ("📈 Ticket Promedio", kpis.get('ticket_promedio', 0), PALETA['rosa']),
            ("🎯 Conversion", kpis.get('conversion', 0), PALETA['lima']),
            ("⚡ Crecimiento", kpis.get('crecimiento', 0), PALETA['alerta']),
        ]

        for titulo, valor, color in kpi_data:
            card = KPICard(titulo, valor, color_acento=color)
            self.kpi_layout.addWidget(card)

        # Filtrar datos
        datos = [
            item for item in analisis
            if isinstance(item.get("top"), dict) and
            (filtro == "Todos" or item.get("columna") == filtro)
        ]

        if not datos:
            aviso = QLabel("⚠️ No hay datos para mostrar en este filtro")
            aviso.setStyleSheet(f"color: {PALETA['texto_secundario']}; font-size: 18px; background: transparent;")
            aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(aviso, 0, 0)
            self.status.setText("⚠️ Sin datos para mostrar")
            self.tabla.setRowCount(0)
            return

        # ===== GRAFICOS - Layout optimizado =====
        fila = 0
        col = 0
        max_cols = 2  # 2 columnas para mejor visualizacion

        for idx, item in enumerate(datos):
            try:
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: {PALETA['fondo_card']};
                        border-radius: 16px;
                        border: 1px solid {PALETA['borde']};
                    }}
                    QFrame:hover {{
                        border: 1px solid {PALETA['acento']};
                    }}
                """)
                card_layout = QVBoxLayout(card)
                card_layout.setSpacing(12)
                card_layout.setContentsMargins(18, 18, 18, 18)

                # Header del card
                header_layout = QHBoxLayout()

                titulo_lbl = QLabel(f"📌 {item.get('columna', 'Sin nombre')}")
                titulo_lbl.setStyleSheet(f"color: white; font-size: 16px; font-weight: bold; background: transparent;")
                header_layout.addWidget(titulo_lbl)

                cantidad = len(item.get("top", {}))
                badge = QLabel(f"{cantidad} items")
                badge.setStyleSheet(f"""
                    color: {PALETA['acento']};
                    background-color: {PALETA['acento']}20;
                    padding: 5px 14px;
                    border-radius: 14px;
                    font-size: 11px;
                    font-weight: bold;
                """)
                header_layout.addWidget(badge)
                header_layout.addStretch()

                # Tipo de grafico badge
                tipo_badge = QLabel(f"📊 {tipo_grafico if tipo_grafico != 'Auto (Recomendado)' else 'Auto'}")
                tipo_badge.setStyleSheet(f"""
                    color: {PALETA['exito']};
                    background-color: {PALETA['exito']}20;
                    padding: 5px 14px;
                    border-radius: 14px;
                    font-size: 10px;
                    font-weight: bold;
                """)
                header_layout.addWidget(tipo_badge)

                card_layout.addLayout(header_layout)

                # Separador
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet(f"background-color: {PALETA['borde']}; max-height: 1px;")
                card_layout.addWidget(sep)

                # Grafico
                top = dict(list(item["top"].items())[:10])
                grafico_func = self.seleccionar_tipo_grafico(item, tipo_grafico, idx)

                if tipo_grafico == "Gauge / Velocimetro":
                    fig = grafico_func(top, item.get("columna", ""))
                else:
                    fig = grafico_func(top, item.get("columna", ""))

                canvas = FigureCanvas(fig)
                canvas.setMinimumHeight(400)
                canvas.setMinimumWidth(520)
                canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                card_layout.addWidget(canvas, 1)

                # Stats footer
                if top:
                    valores = list(top.values())
                    stats_layout = QHBoxLayout()
                    stats_layout.setSpacing(20)

                    max_lbl = QLabel(f"🔺 Max: {max(valores):,.0f}")
                    max_lbl.setStyleSheet(f"color: {PALETA['exito']}; font-size: 11px; background: transparent; font-weight: bold;")
                    stats_layout.addWidget(max_lbl)

                    prom = sum(valores) / len(valores)
                    avg_lbl = QLabel(f"➗ Prom: {prom:,.0f}")
                    avg_lbl.setStyleSheet(f"color: {PALETA['acento']}; font-size: 11px; background: transparent; font-weight: bold;")
                    stats_layout.addWidget(avg_lbl)

                    min_lbl = QLabel(f"🔻 Min: {min(valores):,.0f}")
                    min_lbl.setStyleSheet(f"color: {PALETA['peligro']}; font-size: 11px; background: transparent; font-weight: bold;")
                    stats_layout.addWidget(min_lbl)

                    total_lbl = QLabel(f"📊 Total: {sum(valores):,.0f}")
                    total_lbl.setStyleSheet(f"color: {PALETA['info']}; font-size: 11px; background: transparent; font-weight: bold;")
                    stats_layout.addWidget(total_lbl)

                    stats_layout.addStretch()
                    card_layout.addLayout(stats_layout)

                self.grid.addWidget(card, fila, col)

                col += 1
                if col >= max_cols:
                    col = 0
                    fila += 1

            except Exception as e:
                print(f"Error grafico {item.get('columna', 'desconocido')}: {e}")

        self.status.setText(f"✅ {len(datos)} visualizaciones cargadas | {datetime.now().strftime('%H:%M:%S')}")

        # Actualizar tabla
        self._actualizar_tabla(datos)

    def _actualizar_tabla(self, datos):
        if not datos:
            self.tabla.setRowCount(0)
            return

        filas = []
        for item in datos:
            col_name = item.get("columna", "")
            for key, val in list(item.get("top", {}).items())[:20]:
                total = sum(item['top'].values())
                filas.append({
                    "Columna": col_name,
                    "Item": key,
                    "Valor": f"{val:,.0f}",
                    "%": f"{(val/total*100):.1f}%" if total else "0%",
                    "Ranking": ""
                })

        # Ordenar por valor descendente
        filas.sort(key=lambda x: float(x["Valor"].replace(",", "")), reverse=True)

        # Asignar ranking
        for i, fila in enumerate(filas):
            fila["Ranking"] = f"#{i+1}"

        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["#", "Columna", "Item", "Valor", "%"])
        self.tabla.setRowCount(len(filas))

        for i, fila in enumerate(filas):
            for j, key in enumerate(["Ranking", "Columna", "Item", "Valor", "%"]):
                item = QTableWidgetItem(str(fila[key]))
                if key in ("Valor", "%"):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if key == "Ranking":
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    if i < 3:
                        item.setForeground(QtGui.QColor(PALETA['exito'] if i == 0 else PALETA['alerta'] if i == 1 else PALETA['acento']))
                        item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                self.tabla.setItem(i, j, item)

        self.tabla.resizeColumnsToContents()

    def exportar_pdf_ui(self):
        try:
            from services.export_pdf import exportar_pdf
            exportar_pdf(self.resultado)
            QMessageBox.information(self, "PDF", "✅ Reporte generado correctamente")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ Error al generar PDF:\\n{e}")


# =============================================================================
# 🏁 EJECUCION CON DATOS DE EJEMPLO MEJORADOS
# =============================================================================

if __name__ == "__main__":
    import sys
    from PyQt5.QtGui import QFont

    datos_ejemplo = {
        "kpis": {
            "ventas_totales": 154320.50,
            "tickets_totales": 3421,
            "registros": 15000,
            "clientes_totales": 892,
            "productos_vendidos": 5234,
            "ticket_promedio": 45.11,
            "conversion": 68.5,
            "crecimiento": 23.4
        },
        "analisis": [
            {
                "columna": "Productos Top",
                "top": {"Laptop Dell XPS": 45000, "iPhone 15 Pro": 38000, "Monitor 4K LG": 22000,
                       "Teclado Mecanico": 15000, "Mouse Logitech": 12000, "Webcam HD": 8000, 
                       "Auriculares Sony": 6000, "Hub USB-C": 4000, "Soporte Monitor": 3500, "Cable HDMI": 2800}
            },
            {
                "columna": "Ciudades",
                "top": {"Madrid": 52000, "Barcelona": 41000, "Valencia": 28000,
                       "Sevilla": 19000, "Bilbao": 14000, "Malaga": 11000, "Zaragoza": 8500, "Murcia": 6200}
            },
            {
                "columna": "Vendedores Estrella",
                "top": {"Carlos Ruiz": 35000, "Ana Martinez": 32000, "Luis Garcia": 28000,
                       "Maria Lopez": 24000, "Pedro Sanchez": 19000, "Laura Torres": 15000,
                       "Juan Perez": 12000, "Sofia Diaz": 9500}
            },
            {
                "columna": "Categorias",
                "top": {"Electronica": 85000, "Hogar": 42000, "Deportes": 18000, 
                       "Jardin": 12000, "Libros": 9000, "Juguetes": 7500, "Moda": 6800, "Alimentacion": 5200}
            },
            {
                "columna": "Ventas Mensuales",
                "top": {"Enero": 12000, "Febrero": 15000, "Marzo": 18000, "Abril": 22000, 
                       "Mayo": 28000, "Junio": 32000, "Julio": 35000, "Agosto": 31000, 
                       "Septiembre": 26000, "Octubre": 21000, "Noviembre": 19000, "Diciembre": 24000}
            },
            {
                "columna": "Canales de Venta",
                "top": {"Online": 65000, "Tienda Fisica": 42000, "Telefonico": 18000, 
                       "Redes Sociales": 15000, "Marketplace": 12000, "Email": 8500, "Whatsapp": 6200}
            },
            {
                "columna": "Segmentos Cliente",
                "top": {"Premium": 45000, "Standard": 38000, "Basico": 22000, 
                       "Empresas": 18000, "Startups": 12000, "Freelance": 8500, "Estudiantes": 5200}
            },
            {
                "columna": "Metodos de Pago",
                "top": {"Tarjeta Credito": 52000, "Transferencia": 28000, "PayPal": 18000, 
                       "Efectivo": 12000, "Bizum": 9500, "Cripto": 3500, "Cuotas": 2800}
            },
            {
                "columna": "Satisfaccion Cliente",
                "top": {"Excelente": 420, "Muy Bueno": 380, "Bueno": 220, 
                       "Regular": 120, "Malo": 45, "Pesimo": 12}
            },
            {
                "columna": "Devoluciones",
                "top": {"Producto Danado": 45, "No Coincide": 32, "Arrepentimiento": 28, 
                       "Talla Incorrecta": 22, "Defecto Fabrica": 18, "Otro": 12}
            }
        ]
    }

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    dashboard = Dashboard(datos_ejemplo)
    dashboard.show()

    sys.exit(app.exec_())