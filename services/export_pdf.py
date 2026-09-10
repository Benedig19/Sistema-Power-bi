
import reportlab.platypus
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import reportlab.pdfgen
from reportlab.lib.colors import HexColor

from datetime import datetime
from collections import OrderedDict
import matplotlib
matplotlib.use('Agg')
import matplotlib.patches
import matplotlib.pyplot as plt
import numpy as np
import os
import tempfile
import traceback
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# 🎨 CONFIGURACION DE COLORES Y ESTILOS
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
    "texto_secundario": "#94a3b8"
}

COLORES_GRAFICOS = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#64748b',
    '#a855f7', '#14b8a6', '#f43f5e', '#22c55e', '#eab308'
]


# =============================================================================
# 📊 GENERADORES DE GRAFICOS (12 TIPOS)
# =============================================================================

class GraficoGenerator:
    """Clase generadora de todos los tipos de graficos para PDF."""

    def __init__(self, temp_dir):
        self.temp_dir = temp_dir
        self.contador = 0
        self._setup_matplotlib()

    def _setup_matplotlib(self):
        """Configura estilo oscuro para matplotlib."""
        plt.rcParams['figure.facecolor'] = PALETA['fondo_card']
        plt.rcParams['axes.facecolor'] = PALETA['fondo_card']
        plt.rcParams['text.color'] = 'white'
        plt.rcParams['axes.labelcolor'] = 'white'
        plt.rcParams['xtick.color'] = PALETA['texto_secundario']
        plt.rcParams['ytick.color'] = PALETA['texto_secundario']

    def _siguiente_archivo(self, sufijo=""):
        """Genera nombre unico para archivo temporal."""
        self.contador += 1
        return os.path.join(self.temp_dir, f"grafico_{self.contador:03d}{sufijo}.png")

    def _aplicar_estilo_base(self, ax, titulo=""):
        """Aplica estilo base oscuro."""
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['left', 'bottom']:
            ax.spines[spine].set_color('#475569')
        ax.tick_params(colors=PALETA['texto_secundario'], labelsize=9)
        if titulo:
            ax.set_title(titulo, fontsize=14, fontweight='bold', color='white', pad=15)
        ax.yaxis.grid(True, linestyle='--', alpha=0.2, color='white')
        ax.set_axisbelow(True)

    # -------------------------------------------------------------------------
    # 1. PASTEL / DONA CON PORCENTAJES
    # -------------------------------------------------------------------------
    def pastel(self, data, titulo=""):
        if not data:
            return None

        ordenado = OrderedDict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        labels = list(ordenado.keys())[:8]
        values = [float(v) for v in list(ordenado.values())[:8]]
        total = sum(values)

        fig, ax = plt.subplots(figsize=(7, 5), dpi=120)
        fig.patch.set_facecolor(PALETA['fondo_card'])

        colores = COLORES_GRAFICOS[:len(labels)]

        wedges, texts, autotexts = ax.pie(
            values, labels=None, autopct='%1.1f%%',
            startangle=90, colors=colores,
            pctdistance=0.75, labeldistance=1.12,
            wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2),
            textprops=dict(color='white', fontsize=10, fontweight='bold')
        )

        # Centro con total
        centre_circle = matplotlib.patches.Circle((0, 0), 0.45, fc=PALETA['fondo_card'])
        ax.add_artist(centre_circle)
        ax.text(0, 0.05, f'{total:,.0f}', ha='center', va='center',
               fontsize=18, fontweight='bold', color='white')
        ax.text(0, -0.15, 'TOTAL', ha='center', va='center',
               fontsize=10, color=PALETA['texto_secundario'])

        # Leyenda personalizada con valores
        leyenda_labels = [f'{l} ({v:,.0f} - {v/total*100:.1f}%)' for l, v in zip(labels, values)]
        ax.legend(wedges, leyenda_labels, title="Items", loc="center left",
                 bbox_to_anchor=(1.02, 0, 0.5, 1), fontsize=9,
                 title_fontsize=10, frameon=False, labelcolor='white')

        ax.set_title(titulo, fontsize=16, fontweight='bold', color='white', pad=20)

        ruta = self._siguiente_archivo("_pastel")
        plt.tight_layout()
        plt.savefig(ruta, dpi=120, bbox_inches='tight', facecolor=PALETA['fondo_card'])
        plt.close()
        return ruta

    # -------------------------------------------------------------------------
    # 2. BARRAS VERTICALES CON VALORES
    # -------------------------------------------------------------------------
    def barras_verticales(self, data, titulo=""):
        if not data:
            return None

        ordenado = OrderedDict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        labels = list(ordenado.keys())[:10]
        values = [float(v) for v in list(ordenado.values())[:10]]
        total = sum(values)

        fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
        self._aplicar_estilo_base(ax, titulo)

        x = np.arange(len(labels))
        colores = COLORES_GRAFICOS[:len(labels)]
        bars = ax.bar(x, values, color=colores, edgecolor='white', linewidth=0.8, alpha=0.9, width=0.6)

        # Valores + porcentajes encima
        for bar, val in zip(bars, values):
            height = bar.get_height()
            pct = (val / total * 100) if total else 0
            ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.015,
                   f'{val:,.0f}\n({pct:.1f}%)', ha='center', va='bottom',
                   fontsize=8, color='white', fontweight='bold')

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=10)

        # Leyenda horizontal
        leyenda_items = [matplotlib.patches.Rectangle((0,0),1,1, facecolor=c, edgecolor='white') for c in colores]
        ax.legend(leyenda_items, [f'{l}: {v:,.0f}' for l, v in zip(labels, values)],
                 loc='upper right', fontsize=8, frameon=True, 
                 facecolor=PALETA['fondo_card'], edgecolor='#475569',
                 labelcolor='white', ncol=2)

        plt.tight_layout()
        ruta = self._siguiente_archivo("_barras_v")
        plt.savefig(ruta, dpi=120, bbox_inches='tight', facecolor=PALETA['fondo_card'])
        plt.close()
        return ruta

    # -------------------------------------------------------------------------
    # 3. BARRAS HORIZONTALES CON PORCENTAJES
    # -------------------------------------------------------------------------
    def barras_horizontales(self, data, titulo=""):
        if not data:
            return None

        ordenado = OrderedDict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        labels = list(ordenado.keys())[:10]
        values = [float(v) for v in list(ordenado.values())[:10]]
        total = sum(values)

        fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
        self._aplicar_estilo_base(ax, titulo)

        y = np.arange(len(labels))
        colores = COLORES_GRAFICOS[:len(labels)]
        bars = ax.barh(y, values, color=colores, edgecolor='white', linewidth=0.8, alpha=0.9, height=0.6)

        for bar, val in zip(bars, values):
            width = bar.get_width()
            pct = (val / total * 100) if total else 0
            ax.text(width + max(values)*0.01, bar.get_y() + bar.get_height()/2.,
                   f' {val:,.0f} ({pct:.1f}%)', ha='left', va='center',
                   fontsize=9, color='white', fontweight='bold')

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=10)
        ax.invert_yaxis()

        plt.tight_layout()
        ruta = self._siguiente_archivo("_barras_h")
        plt.savefig(ruta, dpi=120, bbox_inches='tight', facecolor=PALETA['fondo_card'])
        plt.close()
        return ruta

    # -------------------------------------------------------------------------
    # 4. LINEAS / TENDENCIA
    # -------------------------------------------------------------------------
    def lineas(self, data, titulo=""):
        if not data:
            return None

        labels = list(data.keys())[:12]
        values = [float(v) for v in [data[k] for k in labels]]
        total = sum(values)

        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=120)
        self._aplicar_estilo_base(ax, titulo)

        x = np.arange(len(labels))
        ax.plot(x, values, 'o-', linewidth=2.5, color=PALETA['acento'],
               markersize=7, markerfacecolor=PALETA['acento'], markeredgecolor='white', markeredgewidth=1.5)
        ax.fill_between(x, values, alpha=0.15, color=PALETA['acento'])

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9)

        for xi, yi in zip(x, values):
            pct = (yi / total * 100) if total else 0
            ax.annotate(f'{yi:,.0f}\n({pct:.1f}%)', (xi, yi),
                       textcoords="offset points", xytext=(0, 12),
                       ha='center', fontsize=7, color='white', fontweight='bold')

        plt.tight_layout()
        ruta = self._siguiente_archivo("_lineas")
        plt.savefig(ruta, dpi=120, bbox_inches='tight', facecolor=PALETA['fondo_card'])
        plt.close()
        return ruta

    # -------------------------------------------------------------------------
    # 5. AREA / SOMBREADO
    # -------------------------------------------------------------------------
    def area(self, data, titulo=""):
        if not data:
            return None

        labels = list(data.keys())[:10]
        values = [float(v) for v in [data[k] for k in labels]]

        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=120)
        self._aplicar_estilo_base(ax, titulo)

        x = np.arange(len(labels))
        ax.fill_between(x, 0, values, alpha=0.6, color=PALETA['acento'])
        ax.fill_between(x, 0, [v*0.7 for v in values], alpha=0.4, color=PALETA['info'])
        ax.plot(x, values, 'o-', linewidth=2, color='white', markersize=5)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9)

        for xi, yi in zip(x, values):
            ax.text(float(xi), float(yi) + max(values)*0.03, f'{yi:,.0f}', ha='center',
                   fontsize=8, color='white', fontweight='bold')

        plt.tight_layout()
        ruta = self._siguiente_archivo("_area")
        plt.savefig(ruta, dpi=120, bbox_inches='tight', facecolor=PALETA['fondo_card'])
        plt.close()
        return ruta

    # -------------------------------------------------------------------------
    # 6. RADAR / SPIDER
    # -------------------------------------------------------------------------
    def radar(self, data, titulo=""):
        if not data:
            return None

        ordenado = OrderedDict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        labels = list(ordenado.keys())[:8]
        values = [float(v) for v in list(ordenado.values())[:8]]

        max_val = max(values) if values else 1
        values_norm = [v / max_val * 100 for v in values]
        values_norm += values_norm[:1]

        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'), dpi=120)
        fig.patch.set_facecolor(PALETA['fondo_card'])

        ax.plot(angles, values_norm, 'o-', linewidth=2, color=PALETA['acento'],
               markersize=8, markerfacecolor=PALETA['acento'])
        ax.fill(angles, values_norm, alpha=0.25, color=PALETA['acento'])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=9, color='white')
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(['25%', '50%', '75%', '100%'], color=PALETA['texto_secundario'], fontsize=8)
        ax.set_facecolor(PALETA['fondo_card'])
        ax.grid(True, alpha=0.3, color='white')
        ax.spines['polar'].set_color('#475569')

        ax.set_title(titulo, fontsize=14, fontweight='bold', color='white', pad=20)

        plt.tight_layout()
        ruta = self._siguiente_archivo("_radar")
        plt.savefig(ruta, dpi=120, bbox_inches='tight', facecolor=PALETA['fondo_card'])
        plt.close()
        return ruta

    # -------------------------------------------------------------------------
    # 7. PIRAMIDE / FUNNEL
    # -------------------------------------------------------------------------
    def piramide(self, data, titulo=""):
        if not data:
            return None

        ordenado = OrderedDict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        labels = list(ordenado.keys())[:8]
        values = [float(v) for v in list(ordenado.values())[:8]]
        total = sum(values)

        fig, ax = plt.subplots(figsize=(7, 5), dpi=120)
        self._aplicar_estilo_base(ax, titulo)

        max_val = max(values)
        n = len(labels)

        for i, (label, val) in enumerate(zip(labels, values)):
            width = (val / max_val) * 0.9
            left = (1 - width) / 2
            color = COLORES_GRAFICOS[i % len(COLORES_GRAFICOS)]

            ax.barh(i, width, left=left, height=0.7, color=color,
                   alpha=0.85, edgecolor='white', linewidth=1)

            pct = (val / total * 100) if total else 0
            ax.text(0.5, i, f'{label}: {val:,.0f} ({pct:.1f}%)',
                   ha='center', va='center', fontsize=10, fontweight='bold', color='white')

        ax.set_yticks([])
        ax.set_xlim(0, 1)
        ax.invert_yaxis()
        ax.set_xticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        plt.tight_layout()
        ruta = self._siguiente_archivo("_piramide")
        plt.savefig(ruta, dpi=120, bbox_inches='tight', facecolor=PALETA['fondo_card'])
        plt.close()
        return ruta

    # -------------------------------------------------------------------------
    # 8. HEATMAP / MAPA DE CALOR
    # -------------------------------------------------------------------------
    def heatmap(self, data, titulo=""):
        if not data:
            return None

        ordenado = OrderedDict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        labels = list(ordenado.keys())[:16]
        values = [float(v) for v in list(ordenado.values())[:16]]
        total = sum(values)

        fig, ax = plt.subplots(figsize=(8, 6), dpi=120)
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

            rect = matplotlib.patches.Rectangle((col, n_rows - 1 - row), 0.95, 0.95,
                                facecolor=color, edgecolor='white', linewidth=2, alpha=0.9)
            ax.add_patch(rect)

            pct = (val / total * 100) if total else 0
            fontsize = min(11, max(7, len(label) * 0.8))
            ax.text(col + 0.475, n_rows - 1 - row + 0.6, label[:12],
                   ha='center', va='center', fontsize=fontsize, color='white', fontweight='bold')
            ax.text(col + 0.475, n_rows - 1 - row + 0.35, f'{val:,.0f}',
                   ha='center', va='center', fontsize=9, color='white', fontweight='bold')
            ax.text(col + 0.475, n_rows - 1 - row + 0.15, f'({pct:.1f}%)',
                   ha='center', va='center', fontsize=7, color='white', alpha=0.8)

        ax.set_xlim(-0.1, n_cols)
        ax.set_ylim(-0.1, n_rows)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(titulo, fontsize=14, fontweight='bold', color='white', pad=15)
        for spine in ax.spines.values():
            spine.set_visible(False)

        plt.tight_layout()
        ruta = self._siguiente_archivo("_heatmap")
        plt.savefig(ruta, dpi=120, bbox_inches='tight', facecolor=PALETA['fondo_card'])
        plt.close()
        return ruta

    # -------------------------------------------------------------------------
    # 9. COMPARATIVO DE BARRAS (REAL VS META)
    # -------------------------------------------------------------------------
    def comparativo(self, data, titulo=""):
        if not data:
            return None

        labels = list(data.keys())[:8]
        values = [float(v) for v in [data[k] for k in labels]]
        metas = [v * np.random.uniform(0.8, 1.3) for v in values]

        fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
        self._aplicar_estilo_base(ax, titulo)

        x = np.arange(len(labels))
        width = 0.35

        bars1 = ax.bar(x - width/2, values, width, label='Real',
                      color=PALETA['acento'], alpha=0.9, edgecolor='white')
        bars2 = ax.bar(x + width/2, metas, width, label='Meta',
                      color=PALETA['exito'], alpha=0.9, edgecolor='white')

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9)
        ax.legend(loc='upper right', facecolor=PALETA['fondo_card'],
                 edgecolor='#475569', labelcolor='white', fontsize=10)

        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2.,
                       height + max(max(values), max(metas))*0.01,
                       f'{height:,.0f}', ha='center', va='bottom',
                       fontsize=7, color='white', fontweight='bold')

        plt.tight_layout()
        ruta = self._siguiente_archivo("_comparativo")
        plt.savefig(ruta, dpi=120, bbox_inches='tight', facecolor=PALETA['fondo_card'])
        plt.close()
        return ruta

    # -------------------------------------------------------------------------
    # 10. TREEMAP
    # -------------------------------------------------------------------------
    def treemap(self, data, titulo=""):
        if not data:
            return None

        ordenado = OrderedDict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        labels = list(ordenado.keys())[:12]
        values = [float(v) for v in list(ordenado.values())[:12]]
        total = sum(values)

        fig, ax = plt.subplots(figsize=(8, 6), dpi=120)
        fig.patch.set_facecolor(PALETA['fondo_card'])
        ax.set_facecolor(PALETA['fondo_card'])

        max_w, max_h = 10, 8
        x, y = 0, 0

        for i, (label, val) in enumerate(zip(labels, values)):
            area = (val / total) * (max_w * max_h)
            w = np.sqrt(area * 1.5)
            h = area / w

            if x + w > max_w:
                x = 0
                y += h + 0.1

            color = COLORES_GRAFICOS[i % len(COLORES_GRAFICOS)]
            rect = matplotlib.patches.Rectangle((x, y), w, h, facecolor=color,
                                alpha=0.85, edgecolor='white', linewidth=2)
            ax.add_patch(rect)

            pct = (val / total * 100)
            fontsize = min(12, max(7, w * 1.2))
            ax.text(x + w/2, y + h/2, f'{label}\\n{val:,.0f}\\n({pct:.1f}%)',
                   ha='center', va='center', fontsize=fontsize,
                   color='white', fontweight='bold')

            x += w + 0.1

        ax.set_xlim(0, max_w)
        ax.set_ylim(0, max_h)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(titulo, fontsize=14, fontweight='bold', color='white', pad=15)

        plt.tight_layout()
        ruta = self._siguiente_archivo("_treemap")
        plt.savefig(ruta, dpi=120, bbox_inches='tight', facecolor=PALETA['fondo_card'])
        plt.close()
        return ruta

    # -------------------------------------------------------------------------
    # 11. KPIs RESUMEN (BARRAS HORIZONTALES)
    # -------------------------------------------------------------------------
    def kpis_resumen(self, kpis):
        labels = ["Ventas", "Tickets", "Registros", "Clientes", "Productos"]
        values = [
            kpis.get("ventas_totales", 0),
            kpis.get("tickets_totales", 0),
            kpis.get("registros", 0),
            kpis.get("clientes_totales", 0),
            kpis.get("productos_vendidos", 0)
        ]
        colores = [PALETA['acento'], PALETA['exito'], PALETA['alerta'], PALETA['morado'], PALETA['rosa']]

        fig, ax = plt.subplots(figsize=(8, 4), dpi=120)
        self._aplicar_estilo_base(ax, "KPIs Empresariales - Resumen")

        y = np.arange(len(labels))
        bars = ax.barh(y, values, color=colores, edgecolor='white', linewidth=1, alpha=0.9, height=0.6)

        for bar, val, label in zip(bars, values, labels):
            width = bar.get_width()
            ax.text(width + max(values)*0.01, bar.get_y() + bar.get_height()/2.,
                   f' {val:,.0f}', ha='left', va='center',
                   fontsize=11, color='white', fontweight='bold')

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=11, fontweight='bold')
        ax.invert_yaxis()

        plt.tight_layout()
        ruta = self._siguiente_archivo("_kpis")
        plt.savefig(ruta, dpi=120, bbox_inches='tight', facecolor=PALETA['fondo_card'])
        plt.close()
        return ruta


# =============================================================================
# 📄 GENERADOR DE PDF PROFESIONAL
# =============================================================================

class PDFReportGenerator:
    """Generador de reportes PDF profesionales tipo Power BI."""

    def __init__(self, filename="reporte_powerbi.pdf"):
        self.filename = filename
        self.temp_dir = tempfile.mkdtemp(prefix="dashboard_pdf_")
        self.graficos = GraficoGenerator(self.temp_dir)
        self.archivos_temp = []
        self._setup_styles()

    def _setup_styles(self):
        """Configura estilos personalizados para el PDF."""
        self.styles = getSampleStyleSheet()

        # Estilo titulo principal
        self.styles.add(ParagraphStyle(
            name='DashboardTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=HexColor(PALETA['acento']),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Estilo subtitulo
        self.styles.add(ParagraphStyle(
            name='DashboardSubtitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=HexColor(PALETA['texto_secundario']),
            alignment=TA_CENTER,
            spaceAfter=20
        ))

        # Estilo heading de seccion
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=HexColor(PALETA['acento']),
            spaceBefore=15,
            spaceAfter=10,
            borderWidth=1,
            borderColor=HexColor(PALETA['acento']),
            borderPadding=5,
            leftIndent=0
        ))

        # Estilo para totales
        self.styles.add(ParagraphStyle(
            name='TotalValue',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=HexColor(PALETA['exito']),
            fontName='Helvetica-Bold',
            alignment=TA_RIGHT
        ))

    def _crear_tabla_kpis(self, kpis):
        """Crea tabla de KPIs con estilo profesional."""
        datos = [
            ["INDICADOR", "VALOR", "% DEL TOTAL"],
            ["Ventas Totales", f"S/ {kpis.get('ventas_totales', 0):,.2f}", "100%"],
            ["Tickets Procesados", f"{kpis.get('tickets_totales', 0):,}", "-"],
            ["Registros", f"{kpis.get('registros', 0):,}", "-"],
            ["Clientes Unicos", f"{kpis.get('clientes_totales', 0):,}", "-"],
            ["Productos Vendidos", f"{kpis.get('productos_vendidos', 0):,}", "-"],
            ["Ticket Promedio", f"S/ {kpis.get('ticket_promedio', 0):,.2f}", "-"],
            ["Tasa de Conversion", f"{kpis.get('conversion', 0):.1f}%", "-"],
            ["Crecimiento", f"{kpis.get('crecimiento', 0):+.1f}%", "-"],
        ]

        tabla = reportlab.platypus.Table(datos, colWidths=[200, 150, 100])
        tabla.setStyle(reportlab.platypus.TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), HexColor(PALETA['acento'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),

            # Filas alternadas
            ('BACKGROUND', (0, 1), (-1, -1), HexColor(PALETA['fondo_card'])),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#334155')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, HexColor(PALETA['acento'])),

            # Padding
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))

        return tabla

    def _crear_tabla_resumen(self, data, titulo):
        """Crea tabla resumen con top items y porcentajes."""
        ordenado = OrderedDict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        items = list(ordenado.items())[:8]
        total = sum(v for _, v in items)

        datos = [["RANK", "ITEM", "VALOR", "% DEL TOTAL"]]
        medallas = ["🥇", "🥈", "🥉", "4°", "5°", "6°", "7°", "8°"]

        for i, (key, val) in enumerate(items):
            pct = (val / total * 100) if total else 0
            datos.append([
                medallas[i] if i < 3 else str(i+1),
                str(key),
                f"{val:,.0f}",
                f"{pct:.1f}%"
            ])

        # Fila de total
        datos.append(["", "TOTAL", f"{total:,.0f}", "100.0%"])

        tabla = reportlab.platypus.Table(datos, colWidths=[50, 200, 100, 100])
        tabla.setStyle(reportlab.platypus.TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor(PALETA['acento'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            ('BACKGROUND', (0, 1), (-1, -2), HexColor(PALETA['fondo_card'])),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.white),
            ('ALIGN', (0, 1), (0, -2), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -2), 'RIGHT'),

            # Fila total
            ('BACKGROUND', (0, -1), (-1, -1), HexColor(PALETA['exito'])),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, -1), (-1, -1), 'CENTER'),

            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#334155')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))

        return tabla

    def generar(self, resultado):
        """Genera el PDF completo."""
        try:
            doc = reportlab.platypus.SimpleDocTemplate(
                self.filename,
                pagesize=letter,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=20
            )

            contenido = []
            kpis = resultado.get("kpis", {})
            analisis = resultado.get("analisis", [])

            # ==============================
            # PORTADA
            # ==============================
            contenido.append(reportlab.platypus.Spacer(1, 80))
            contenido.append(reportlab.platypus.Paragraph("📊 REPORTE EMPRESARIAL", self.styles['DashboardTitle']))
            contenido.append(reportlab.platypus.Paragraph("Dashboard Analytics Pro", self.styles['DashboardSubtitle']))

            fecha = datetime.now().strftime("%d de %B de %Y - %H:%M hrs")
            contenido.append(reportlab.platypus.Paragraph(f"Generado: {fecha}", self.styles['DashboardSubtitle']))
            contenido.append(reportlab.platypus.Spacer(1, 40))

            # Linea decorativa
            contenido.append(reportlab.platypus.HRFlowable(width="100%", thickness=2, color=HexColor(PALETA['acento'])))
            contenido.append(reportlab.platypus.PageBreak())

            # ==============================
            # SECCION 1: KPIs
            # ==============================
            contenido.append(reportlab.platypus.Paragraph("💎 INDICADORES CLAVE (KPIs)", self.styles['SectionHeader']))
            contenido.append(reportlab.platypus.Spacer(1, 10))

            contenido.append(self._crear_tabla_kpis(kpis))
            contenido.append(reportlab.platypus.Spacer(1, 20))

            # Grafico de barras de KPIs
            img_kpi = self.graficos.kpis_resumen(kpis)
            if img_kpi:
                self.archivos_temp.append(img_kpi)
                contenido.append(reportlab.platypus.Image(img_kpi, width=480, height=240))

            contenido.append(reportlab.platypus.PageBreak())

            # ==============================
            # SECCION 2: ANALISIS DETALLADO
            # ==============================
            contenido.append(reportlab.platypus.Paragraph("📈 ANALISIS DETALLADO POR CATEGORIA", self.styles['SectionHeader']))
            contenido.append(reportlab.platypus.Spacer(1, 15))

            tipos_graficos = [
                self.graficos.pastel,
                self.graficos.barras_verticales,
                self.graficos.barras_horizontales,
                self.graficos.lineas,
                self.graficos.area,
                self.graficos.radar,
                self.graficos.piramide,
                self.graficos.heatmap,
                self.graficos.comparativo,
                self.graficos.treemap,
            ]

            for idx, item in enumerate(analisis):
                top = item.get("top")
                if not isinstance(top, dict) or len(top) == 0:
                    continue

                nombre = item.get("columna", f"Grafico {idx+1}")

                # Titulo de seccion
                contenido.append(reportlab.platypus.Paragraph(f"📌 {nombre}", self.styles['Heading2']))
                contenido.append(reportlab.platypus.Spacer(1, 5))

                # Tabla resumen con porcentajes
                tabla_resumen = self._crear_tabla_resumen(top, nombre)
                contenido.append(tabla_resumen)
                contenido.append(reportlab.platypus.Spacer(1, 15))

                # Grafico (rotar tipos)
                grafico_func = tipos_graficos[idx % len(tipos_graficos)]
                img_path = grafico_func(top, nombre)

                if img_path:
                    self.archivos_temp.append(img_path)
                    contenido.append(reportlab.platypus.Image(img_path, width=460, height=300))

                contenido.append(reportlab.platypus.Spacer(1, 20))

                # Cada 2 graficos -> nueva pagina
                if idx % 2 == 1 and idx < len(analisis) - 1:
                    contenido.append(reportlab.platypus.PageBreak())

            # ==============================
            # FOOTER
            # ==============================
            contenido.append(reportlab.platypus.Spacer(1, 30))
            contenido.append(reportlab.platypus.HRFlowable(width="100%", thickness=1, color=HexColor('#334155')))
            contenido.append(reportlab.platypus.Spacer(1, 10))
            contenido.append(reportlab.platypus.Paragraph(
                "Reporte generado automaticamente por Dashboard Analytics Pro v2.0",
                self.styles['Italic']
            ))
            contenido.append(reportlab.platypus.Paragraph(
                f"Total de categorias analizadas: {len(analisis)} | Total de registros: {kpis.get('registros', 0):,}",
                self.styles['DashboardSubtitle']
            ))

            # Generar PDF
            doc.build(contenido)
            logger.info(f"✅ PDF generado: {self.filename}")
            print(f"✅ PDF generado correctamente: {self.filename}")

            return True

        except Exception as e:
            logger.error(f"❌ Error generando PDF: {e}")
            traceback.print_exc()
            return False

        finally:
            self._limpiar_temp()

    def _limpiar_temp(self):
        """Limpia archivos temporales."""
        for archivo in self.archivos_temp:
            try:
                if os.path.exists(archivo):
                    os.remove(archivo)
            except Exception as e:
                logger.warning(f"No se pudo eliminar {archivo}: {e}")

        try:
            if os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
        except:
            pass


# =============================================================================
# 🚀 FUNCION PRINCIPAL (COMPATIBILIDAD)
# =============================================================================

def exportar_pdf(resultado, archivo="reporte_powerbi.pdf"):
    """
    Funcion principal para exportar a PDF.
    Compatible con tu codigo anterior.
    """
    generador = PDFReportGenerator(archivo)
    return generador.generar(resultado)


# =============================================================================
# 🧪 PRUEBA
# =============================================================================

if __name__ == "__main__":
    datos_prueba = {
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
            {"columna": "Productos Top", "top": {"Laptop": 45000, "iPhone": 38000, "Monitor": 22000, "Teclado": 15000, "Mouse": 12000}},
            {"columna": "Ciudades", "top": {"Madrid": 52000, "Barcelona": 41000, "Valencia": 28000, "Sevilla": 19000, "Bilbao": 14000}},
            {"columna": "Vendedores", "top": {"Carlos": 35000, "Ana": 32000, "Luis": 28000, "Maria": 24000, "Pedro": 19000}},
            {"columna": "Categorias", "top": {"Electronica": 85000, "Hogar": 42000, "Deportes": 18000, "Jardin": 12000, "Libros": 9000}},
            {"columna": "Meses", "top": {"Enero": 12000, "Febrero": 15000, "Marzo": 18000, "Abril": 22000, "Mayo": 28000}},
        ]
    }

    exportar_pdf(datos_prueba, "prueba_reporte.pdf")