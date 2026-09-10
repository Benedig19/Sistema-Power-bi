import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.figure import Figure
import numpy as np

COLORES = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', 
           '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#64748b']


def _preparar_datos(data_dict):
    """Ordena y limpia datos."""
    if not data_dict:
        return [], []
    
    try:
        ordenado = dict(sorted(data_dict.items(), 
                      key=lambda x: float(x[1]) if isinstance(x[1], (int, float, str)) else 0, 
                      reverse=True))
    except:
        ordenado = data_dict
    
    labels = list(ordenado.keys())[:10]
    values = []
    for v in list(ordenado.values())[:10]:
        try:
            values.append(float(v))
        except:
            values.append(0)
    
    return labels, values


def _setup_axes(fig, ax):
    """Configura fondo oscuro."""
    fig.patch.set_facecolor('#1e293b')
    ax.set_facecolor('#1e293b')
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    for s in ['left', 'bottom']:
        ax.spines[s].set_color('#475569')


# =============================================================================
# 1. BARRAS VERTICALES
# =============================================================================

def crear_barras(data_dict, titulo=""):
    fig = Figure(figsize=(7, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    _setup_axes(fig, ax)
    
    labels, values = _preparar_datos(data_dict)
    
    if not values or sum(values) == 0:
        ax.text(0.5, 0.5, "Sin datos válidos", ha='center', va='center',
               fontsize=14, color='white', fontweight='bold')
        ax.axis('off')
        return fig
    
    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=COLORES[:len(labels)], 
                  edgecolor='white', linewidth=0.5, alpha=0.9, width=0.55)
    
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.015,
               f'{val:,.0f}', ha='center', va='bottom', fontsize=10,
               color='white', fontweight='bold')
    
    ax.set_xticks(x)
    ax.set_xticklabels([str(l)[:15] for l in labels], rotation=35, ha='right', 
                       fontsize=10, color='white')
    ax.tick_params(axis='y', colors='white', labelsize=10)
    ax.set_title(str(titulo)[:30], fontsize=13, fontweight='bold', color='white', pad=15)
    ax.yaxis.grid(True, linestyle='--', alpha=0.25, color='white')
    ax.set_axisbelow(True)
    
    fig.subplots_adjust(left=0.1, right=0.95, top=0.88, bottom=0.28)
    return fig


# =============================================================================
# 2. BARRAS HORIZONTALES
# =============================================================================

def crear_barras_h(data_dict, titulo=""):
    fig = Figure(figsize=(8, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    _setup_axes(fig, ax)
    
    labels, values = _preparar_datos(data_dict)
    
    if not values or sum(values) == 0:
        ax.text(0.5, 0.5, "Sin datos válidos", ha='center', va='center',
               fontsize=14, color='white', fontweight='bold')
        ax.axis('off')
        return fig
    
    y = np.arange(len(labels))
    bars = ax.barh(y, values, color=COLORES[:len(labels)], 
                   edgecolor='white', linewidth=0.5, alpha=0.9, height=0.55)
    
    ax.invert_yaxis()
    
    for bar, val in zip(bars, values):
        width = bar.get_width()
        ax.text(width + max(values)*0.01, bar.get_y() + bar.get_height()/2.,
               f'{val:,.0f}', ha='left', va='center', fontsize=10,
               color='white', fontweight='bold')
    
    ax.set_yticks(y)
    ax.set_yticklabels([str(l)[:20] for l in labels], fontsize=10, color='white')
    ax.tick_params(axis='x', colors='white', labelsize=10)
    ax.set_title(str(titulo)[:30], fontsize=13, fontweight='bold', color='white', pad=15)
    ax.xaxis.grid(True, linestyle='--', alpha=0.25, color='white')
    ax.set_axisbelow(True)
    
    fig.subplots_adjust(left=0.28, right=0.95, top=0.88, bottom=0.12)
    return fig


# =============================================================================
# 3. PASTEL / DONUT
# =============================================================================

def crear_pastel(data_dict, titulo=""):
    fig = Figure(figsize=(7, 5), dpi=100)
    ax = fig.add_subplot(111)
    
    fig.patch.set_facecolor('#1e293b')
    ax.set_facecolor('#1e293b')
    
    if not data_dict:
        ax.text(0.5, 0.5, "Sin datos", ha='center', va='center',
               fontsize=14, color='white', fontweight='bold')
        ax.axis('off')
        return fig
    
    labels, values = _preparar_datos(data_dict)
    
    # Agrupar Otros
    try:
        ordenado = dict(sorted(data_dict.items(), 
                      key=lambda x: float(x[1]) if isinstance(x[1], (int, float, str)) else 0, 
                      reverse=True))
        all_values = list(ordenado.values())
        if len(all_values) > 8:
            otros = sum(float(v) for v in all_values[7:])
            labels = list(ordenado.keys())[:7]
            values = [float(v) for v in all_values[:7]]
            labels.append("Otros")
            values.append(otros)
    except:
        pass
    
    if not values or sum(values) == 0:
        ax.text(0.5, 0.5, "Sin datos válidos", ha='center', va='center',
               fontsize=14, color='white', fontweight='bold')
        ax.axis('off')
        return fig
    
    explode = [0.05 if i == 0 else 0.02 for i in range(len(values))]
    
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct='%1.1f%%', startangle=90,
        colors=COLORES[:len(values)], explode=explode, pctdistance=0.75,
        wedgeprops={'edgecolor': '#1e293b', 'linewidth': 2}
    )
    
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_weight("bold")
        autotext.set_color('white')
    
    # Leyenda con espacio amplio
    legend_labels = [f"{str(lab)[:15]} ({val:,.0f})" for lab, val in zip(labels, values)]
    ax.legend(wedges, legend_labels, title="Categorías", loc="center left",
             bbox_to_anchor=(1.02, 0.5), fontsize=10, frameon=False,
             labelcolor='white')
    
    ax.set_title(str(titulo)[:30], fontsize=13, fontweight='bold', color='white', pad=15)
    ax.axis('equal')
    
    # Márgenes amplios para leyenda
    fig.subplots_adjust(left=0.05, right=0.62, top=0.9, bottom=0.1)
    return fig


# =============================================================================
# 4. LÍNEAS
# =============================================================================

def crear_lineas(data_dict, titulo=""):
    fig = Figure(figsize=(8, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    _setup_axes(fig, ax)
    
    if not data_dict:
        ax.text(0.5, 0.5, "Sin datos", ha='center', va='center',
               fontsize=14, color='white', fontweight='bold')
        ax.axis('off')
        return fig
    
    try:
        items = sorted(data_dict.items(), key=lambda x: str(x[0]))
    except:
        items = list(data_dict.items())
    
    labels = [str(k)[:12] for k, v in items[:15]]
    values = []
    for v in [v for k, v in items[:15]]:
        try:
            values.append(float(v))
        except:
            values.append(0)
    
    if not values:
        ax.text(0.5, 0.5, "Sin datos válidos", ha='center', va='center',
               fontsize=14, color='white', fontweight='bold')
        ax.axis('off')
        return fig
    
    x = np.arange(len(labels))
    
    ax.plot(x, values, color='#3b82f6', linewidth=3, marker='o', markersize=7,
            markerfacecolor='#1e293b', markeredgewidth=2, markeredgecolor='#3b82f6',
            zorder=3)
    ax.fill_between(x, values, alpha=0.2, color='#3b82f6')
    
    if values:
        max_idx = np.argmax(values)
        min_idx = np.argmin(values)
        ax.scatter([max_idx], [values[max_idx]], color='#10b981', s=100, zorder=5)
        ax.scatter([min_idx], [values[min_idx]], color='#ef4444', s=100, zorder=5)
    
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha='right', fontsize=10, color='white')
    ax.tick_params(axis='y', colors='white', labelsize=10)
    ax.set_title(str(titulo)[:30], fontsize=13, fontweight='bold', color='white', pad=15)
    ax.yaxis.grid(True, linestyle='--', alpha=0.25, color='white')
    ax.set_axisbelow(True)
    
    fig.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.25)
    return fig


# =============================================================================
# 5. ÁREA
# =============================================================================

def crear_area(data_dict, titulo=""):
    fig = Figure(figsize=(8, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    _setup_axes(fig, ax)
    
    if not data_dict:
        ax.text(0.5, 0.5, "Sin datos", ha='center', va='center',
               fontsize=14, color='white', fontweight='bold')
        ax.axis('off')
        return fig
    
    try:
        items = sorted(data_dict.items(), key=lambda x: str(x[0]))
    except:
        items = list(data_dict.items())
    
    labels = [str(k)[:12] for k, v in items[:15]]
    values = []
    for v in [v for k, v in items[:15]]:
        try:
            values.append(float(v))
        except:
            values.append(0)
    
    if not values:
        ax.text(0.5, 0.5, "Sin datos válidos", ha='center', va='center',
               fontsize=14, color='white', fontweight='bold')
        ax.axis('off')
        return fig
    
    x = np.arange(len(labels))
    
    ax.fill_between(x, values, alpha=0.4, color='#10b981')
    ax.plot(x, values, color='#10b981', linewidth=2.5, zorder=3)
    
    if len(values) > 2:
        z = np.polyfit(x, values, 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), "--", color='#f59e0b', linewidth=1.5, alpha=0.7, label='Tendencia')
        ax.legend(fontsize=9, frameon=False, labelcolor='white')
    
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha='right', fontsize=10, color='white')
    ax.tick_params(axis='y', colors='white', labelsize=10)
    ax.set_title(str(titulo)[:30], fontsize=13, fontweight='bold', color='white', pad=15)
    ax.yaxis.grid(True, linestyle='--', alpha=0.25, color='white')
    ax.set_axisbelow(True)
    
    fig.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.25)
    return fig


# =============================================================================
# 🎯 FUNCIÓN MAESTRA (usa esta en tu código)
# =============================================================================

def crear_grafico(data_dict, titulo="", tipo='barras', dark_mode=True):
    """Crea gráfico según tipo. Esta es la función que importas."""
    tipo = str(tipo).lower().strip()
    
    if tipo in ('barras_h', 'horizontal', 'barh', 'hbar'):
        return crear_barras_h(data_dict, titulo)
    elif tipo in ('pastel', 'pie', 'torta', 'donut', 'circular'):
        return crear_pastel(data_dict, titulo)
    elif tipo in ('lineas', 'line', 'linea', 'tendencia'):
        return crear_lineas(data_dict, titulo)
    elif tipo in ('area', 'areas'):
        return crear_area(data_dict, titulo)
    else:
        return crear_barras(data_dict, titulo)