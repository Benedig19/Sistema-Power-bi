import matplotlib
matplotlib.use('Agg')  # Backend no-interactivo para PyQt

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Tuple
from datetime import datetime


# =============================================================================
# 🎨 PALETAS DE COLORES
# =============================================================================

PALETAS = {
    'default': ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'],
    'ocean': ['#0ea5e9', '#06b6d4', '#14b8a6', '#10b981', '#22c55e', '#84cc16'],
    'sunset': ['#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e', '#14b8a6'],
    'berry': ['#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e', '#ef4444'],
    'corporate': ['#1e3a8a', '#1d4ed8', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe'],
    'monocromo': ['#0f172a', '#334155', '#64748b', '#94a3b8', '#cbd5e1', '#e2e8f0'],
}


# =============================================================================
# 🧠 UTILIDADES INTERNAS
# =============================================================================

def _aplicar_tema(fig, ax, dark_mode: bool = False):
    """Aplica tema oscuro o claro al gráfico."""
    if dark_mode:
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        ax.tick_params(colors='#cbd5e1')
        ax.xaxis.label.set_color('#f8fafc')
        ax.yaxis.label.set_color('#f8fafc')
        ax.title.set_color('#f8fafc')
        for spine in ax.spines.values():
            spine.set_color('#334155')
    else:
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        ax.tick_params(colors='#1e293b')
        ax.xaxis.label.set_color('#1e293b')
        ax.yaxis.label.set_color('#1e293b')
        ax.title.set_color('#1e293b')
        for spine in ax.spines.values():
            spine.set_color('#e2e8f0')


def _formatear_eje_y(ax):
    """Formatea el eje Y con separadores de miles."""
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:,.0f}'))


def _formatear_eje_fecha(ax, freq: str = 'auto'):
    """
    Formatea el eje X de fechas de forma inteligente según la frecuencia.
    """
    if freq == 'auto':
        # Detectar frecuencia automáticamente
        xlim = ax.get_xlim()
        dias = xlim[1] - xlim[0]
        if dias > 365 * 2:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax.xaxis.set_major_locator(mdates.YearLocator())
        elif dias > 90:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        elif dias > 30:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    elif freq == 'anual':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
    elif freq == 'mensual':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    elif freq == 'semanal':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    elif freq == 'diario':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    
    plt.xticks(rotation=45, ha='right')


def _figura_vacia(mensaje: str = "Sin datos", dark_mode: bool = False, size=(8, 5)):
    """Crea una figura vacía con mensaje cuando no hay datos."""
    fig, ax = plt.subplots(figsize=size)
    _aplicar_tema(fig, ax, dark_mode)
    ax.text(0.5, 0.5, mensaje, ha='center', va='center', fontsize=14, 
            color='#cbd5e1' if dark_mode else '#64748b', fontweight='bold')
    ax.axis('off')
    return fig


def _preparar_df_fechas(df, col_fecha, col_valor, agrupar='D'):
    """
    Prepara un DataFrame agrupando por fecha.
    
    Args:
        agrupar: 'D' diario, 'W' semanal, 'M' mensual, 'Y' anual
    """
    if df.empty or col_fecha not in df.columns or col_valor not in df.columns:
        return pd.DataFrame()
    
    df = df[[col_fecha, col_valor]].copy()
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df = df.dropna()
    
    if df.empty:
        return pd.DataFrame()
    
    # Agrupar según frecuencia
    if agrupar == 'D':
        df = df.groupby(df[col_fecha].dt.date)[col_valor].sum().reset_index()
    elif agrupar == 'W':
        df[col_fecha] = pd.to_datetime(df[col_fecha]).dt.to_period('W').dt.start_time
        df = df.groupby(col_fecha)[col_valor].sum().reset_index()
    elif agrupar == 'M':
        df[col_fecha] = pd.to_datetime(df[col_fecha]).dt.to_period('M').dt.start_time
        df = df.groupby(col_fecha)[col_valor].sum().reset_index()
    elif agrupar == 'Y':
        df[col_fecha] = pd.to_datetime(df[col_fecha]).dt.to_period('Y').dt.start_time
        df = df.groupby(col_fecha)[col_valor].sum().reset_index()
    
    df = df.sort_values(by=col_fecha)
    df[col_fecha] = pd.to_datetime(df[col_fecha])
    
    return df


# =============================================================================
# 📈 GRÁFICO DE LÍNEA MEJORADO
# =============================================================================

def crear_grafico_linea(
    df: pd.DataFrame,
    col_fecha: str,
    col_valor: str,
    titulo: str = "Tendencia",
    dark_mode: bool = False,
    paleta: str = 'default',
    area: bool = False,
    suavizar: bool = False,
    mostrar_puntos: bool = True,
    mostrar_valores: bool = False,
    freq: str = 'auto',
    agrupar: str = 'D',
    size: Tuple[int, int] = (10, 5)
) -> Figure:
    """
    Crea un gráfico de línea temporal profesional.
    
    Args:
        df: DataFrame con los datos
        col_fecha: Nombre de la columna de fechas
        col_valor: Nombre de la columna de valores
        titulo: Título del gráfico
        dark_mode: True para fondo oscuro
        paleta: Nombre de la paleta de colores
        area: True para rellenar el área bajo la línea
        suavizar: True para suavizar la curva con interpolación
        mostrar_puntos: True para mostrar puntos en cada dato
        mostrar_valores: True para mostrar valores encima de cada punto
        freq: Frecuencia del eje X ('auto', 'diario', 'semanal', 'mensual', 'anual')
        agrupar: 'D', 'W', 'M', 'Y' para agrupar datos
        size: Tamaño de la figura (ancho, alto)
    """
    # Preparar datos
    df_plot = _preparar_df_fechas(df, col_fecha, col_valor, agrupar)
    
    if df_plot.empty:
        return _figura_vacia("⚠️ Sin datos válidos", dark_mode, size)
    
    fig, ax = plt.subplots(figsize=size)
    _aplicar_tema(fig, ax, dark_mode)
    
    color = PALETAS.get(paleta, PALETAS['default'])[0]
    fechas = df_plot[col_fecha]
    valores = df_plot[col_valor].astype(float)
    
    # Suavizar con interpolación si se pide
    if suavizar and len(fechas) > 3:
        x_num = mdates.date2num(fechas)
        x_smooth = np.linspace(x_num.min(), x_num.max(), 300)
        # Interpolación lineal para evitar depender de SciPy.
        y_smooth = np.interp(x_smooth, x_num, valores)
        fechas_smooth = mdates.num2date(x_smooth)
        
        if area:
            ax.fill_between(fechas_smooth, y_smooth, alpha=0.25, color=color)
        ax.plot(fechas_smooth, y_smooth, color=color, linewidth=2.5, alpha=0.8)
    else:
        if area:
            ax.fill_between(fechas, valores, alpha=0.25, color=color)
        ax.plot(fechas, valores, color=color, linewidth=2.5)
    
    # Puntos
    if mostrar_puntos:
        ax.scatter(fechas, valores, color=color, s=60, zorder=5, 
                  edgecolor='white' if not dark_mode else '#0f172a', linewidth=2)
    
    # Valores encima de puntos
    if mostrar_valores:
        for fecha, val in zip(fechas, valores):
            ax.annotate(f'{val:,.0f}', (fecha, val), 
                       textcoords="offset points", xytext=(0, 10),
                       ha='center', fontsize=8, fontweight='bold',
                       color='white' if dark_mode else '#1e293b')
    
    # Destacar máximo y mínimo
    # Usar índices posicionales para que `.iloc` no dependa del tipo del índice
    # de la serie (que puede ser entero, texto u otro tipo de etiqueta).
    max_idx = int(np.argmax(valores.to_numpy()))
    min_idx = int(np.argmin(valores.to_numpy()))
    
    ax.scatter([fechas.iloc[max_idx]], [valores.iloc[max_idx]], 
              color='#10b981', s=120, zorder=6, edgecolor='white', linewidth=2)
    ax.scatter([fechas.iloc[min_idx]], [valores.iloc[min_idx]], 
              color='#ef4444', s=120, zorder=6, edgecolor='white', linewidth=2)
    
    # Anotaciones de max/min
    ax.annotate(f'Máx: {valores.iloc[max_idx]:,.0f}', 
               (fechas.iloc[max_idx], valores.iloc[max_idx]),
               textcoords="offset points", xytext=(10, 10),
               fontsize=9, fontweight='bold', color='#10b981')
    ax.annotate(f'Mín: {valores.iloc[min_idx]:,.0f}', 
               (fechas.iloc[min_idx], valores.iloc[min_idx]),
               textcoords="offset points", xytext=(10, -15),
               fontsize=9, fontweight='bold', color='#ef4444')
    
    # Tendencia (línea de regresión)
    if len(fechas) > 2:
        x_num = np.arange(len(fechas))
        z = np.polyfit(x_num, valores, 1)
        p = np.poly1d(z)
        ax.plot(fechas, p(x_num), "--", color='#f59e0b', linewidth=1.5, 
               alpha=0.7, label=f'Tendencia {"▲" if z[0] > 0 else "▼"}')
        ax.legend(fontsize=10, frameon=False, labelcolor='white' if dark_mode else '#1e293b')
    
    # Formato
    ax.set_title(titulo, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Fecha", fontsize=12, fontweight='bold')
    ax.set_ylabel("Valor", fontsize=12, fontweight='bold')
    
    _formatear_eje_y(ax)
    _formatear_eje_fecha(ax, freq)
    
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig


# =============================================================================
# 📊 GRÁFICO DE LÍNEAS MÚLTIPLES (Comparación)
# =============================================================================

def crear_grafico_lineas_multiples(
    df: pd.DataFrame,
    col_fecha: str,
    col_valores: List[str],
    titulo: str = "Comparación",
    dark_mode: bool = False,
    paleta: str = 'default',
    area: bool = False,
    freq: str = 'auto',
    agrupar: str = 'D',
    size: Tuple[int, int] = (10, 6)
) -> Figure:
    """
    Crea un gráfico con múltiples líneas para comparar series.
    
    Args:
        col_valores: Lista de nombres de columnas a comparar
    """
    if df.empty or col_fecha not in df.columns:
        return _figura_vacia("⚠️ Sin datos válidos", dark_mode, size)
    
    fig, ax = plt.subplots(figsize=size)
    _aplicar_tema(fig, ax, dark_mode)
    
    colores = PALETAS.get(paleta, PALETAS['default'])
    
    # Preparar cada serie
    for i, col_valor in enumerate(col_valores):
        if col_valor not in df.columns:
            continue
            
        df_plot = _preparar_df_fechas(df, col_fecha, col_valor, agrupar)
        if df_plot.empty:
            continue
        
        color = colores[i % len(colores)]
        fechas = df_plot[col_fecha]
        valores = df_plot[col_valor].astype(float)
        
        if area:
            ax.fill_between(fechas, valores, alpha=0.15, color=color)
        
        ax.plot(fechas, valores, color=color, linewidth=2.5, 
               label=col_valor, marker='o', markersize=5,
               markerfacecolor='white' if not dark_mode else '#0f172a',
               markeredgewidth=1.5, markeredgecolor=color)
    
    ax.set_title(titulo, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Fecha", fontsize=12, fontweight='bold')
    ax.set_ylabel("Valor", fontsize=12, fontweight='bold')
    
    _formatear_eje_y(ax)
    _formatear_eje_fecha(ax, freq)
    
    ax.legend(fontsize=10, frameon=False, loc='upper left', 
             labelcolor='white' if dark_mode else '#1e293b')
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig


# =============================================================================
# 📊 GRÁFICO DE BARRAS TEMPORALES
# =============================================================================

def crear_grafico_barras_temporal(
    df: pd.DataFrame,
    col_fecha: str,
    col_valor: str,
    titulo: str = "Valores por Período",
    dark_mode: bool = False,
    paleta: str = 'default',
    agrupar: str = 'M',
    freq: str = 'mensual',
    size: Tuple[int, int] = (10, 5)
) -> Figure:
    """
    Crea un gráfico de barras agrupado por período temporal.
    """
    df_plot = _preparar_df_fechas(df, col_fecha, col_valor, agrupar)
    
    if df_plot.empty:
        return _figura_vacia("⚠️ Sin datos válidos", dark_mode, size)
    
    fig, ax = plt.subplots(figsize=size)
    _aplicar_tema(fig, ax, dark_mode)
    
    color = PALETAS.get(paleta, PALETAS['default'])[0]
    fechas = df_plot[col_fecha]
    valores = df_plot[col_valor].astype(float)
    
    x = np.arange(len(fechas))
    bars = ax.bar(x, valores, color=color, alpha=0.85, edgecolor='none', width=0.6)
    
    # Destacar barra más alta
    max_idx = int(np.argmax(valores.to_numpy()))
    bars[max_idx].set_color('#10b981')
    
    # Valores encima
    for bar, val in zip(bars, valores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + (max(valores) * 0.01),
               f'{val:,.0f}', ha='center', va='bottom', fontsize=9,
               color='white' if dark_mode else '#1e293b', fontweight='bold')
    
    ax.set_xticks(x)
    ax.set_xticklabels([f.strftime('%b %Y') if agrupar == 'M' else 
                      f.strftime('%d %b') if agrupar == 'D' else
                      f.strftime('%Y') for f in fechas], 
                     rotation=45, ha='right', fontsize=10)
    
    ax.set_title(titulo, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Período", fontsize=12, fontweight='bold')
    ax.set_ylabel("Valor", fontsize=12, fontweight='bold')
    
    _formatear_eje_y(ax)
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig


# =============================================================================
# 📈 GRÁFICO DE CRECIMIENTO ACUMULADO
# =============================================================================

def crear_grafico_acumulado(
    df: pd.DataFrame,
    col_fecha: str,
    col_valor: str,
    titulo: str = "Crecimiento Acumulado",
    dark_mode: bool = False,
    paleta: str = 'default',
    freq: str = 'auto',
    size: Tuple[int, int] = (10, 5)
) -> Figure:
    """
    Crea un gráfico de área acumulada mostrando el crecimiento total.
    """
    df_plot = _preparar_df_fechas(df, col_fecha, col_valor, 'D')
    
    if df_plot.empty:
        return _figura_vacia("⚠️ Sin datos válidos", dark_mode, size)
    
    fig, ax = plt.subplots(figsize=size)
    _aplicar_tema(fig, ax, dark_mode)
    
    color = PALETAS.get(paleta, PALETAS['default'])[0]
    fechas = df_plot[col_fecha]
    valores = df_plot[col_valor].astype(float).cumsum()
    
    # Área acumulada
    ax.fill_between(fechas, valores, alpha=0.3, color=color)
    ax.plot(fechas, valores, color=color, linewidth=2.5)
    
    # Meta lineal
    total = valores.iloc[-1]
    dias = len(fechas)
    meta_diaria = total / dias
    meta_lineal = [meta_diaria * (i + 1) for i in range(dias)]
    ax.plot(fechas, meta_lineal, '--', color='#f59e0b', linewidth=2, 
           alpha=0.7, label='Meta lineal')
    
    # Valor final
    ax.annotate(f'Total: {total:,.0f}', 
               (fechas.iloc[-1], valores.iloc[-1]),
               textcoords="offset points", xytext=(-10, 10),
               fontsize=11, fontweight='bold', color=color,
               ha='right')
    
    ax.set_title(titulo, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Fecha", fontsize=12, fontweight='bold')
    ax.set_ylabel("Valor Acumulado", fontsize=12, fontweight='bold')
    
    _formatear_eje_y(ax)
    _formatear_eje_fecha(ax, freq)
    
    ax.legend(fontsize=10, frameon=False, labelcolor='white' if dark_mode else '#1e293b')
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig


# =============================================================================
# 🎯 FUNCIÓN MAESTRA (Router)
# =============================================================================

def crear_grafico_temporal(
    df: pd.DataFrame,
    col_fecha: str,
    col_valor: str,
    titulo: str = "Tendencia",
    tipo: str = 'linea',
    **kwargs
) -> Figure:
    """
    Función maestra para gráficos temporales.
    
    Args:
        tipo: 'linea', 'area', 'barras', 'acumulado', 'multiples'
    """
    tipo = tipo.lower().strip()
    
    if tipo in ('linea', 'line', 'lineas'):
        return crear_grafico_linea(df, col_fecha, col_valor, titulo, **kwargs)
    elif tipo in ('area', 'areas'):
        return crear_grafico_linea(df, col_fecha, col_valor, titulo, area=True, **kwargs)
    elif tipo in ('barras', 'bar', 'barras_temporal'):
        return crear_grafico_barras_temporal(df, col_fecha, col_valor, titulo, **kwargs)
    elif tipo in ('acumulado', 'cumulativo', 'stack'):
        return crear_grafico_acumulado(df, col_fecha, col_valor, titulo, **kwargs)
    else:
        return crear_grafico_linea(df, col_fecha, col_valor, titulo, **kwargs)


# =============================================================================
# 🧹 LIMPIEZA DE MEMORIA
# =============================================================================

def cerrar_figura(fig: Figure):
    """Cierra figura para liberar memoria en PyQt."""
    if fig is not None:
        plt.close(fig)


# =============================================================================
# 📝 EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Datos de ejemplo
    fechas = pd.date_range(start='2024-01-01', periods=30, freq='D')
    np.random.seed(42)
    ventas = np.random.randint(5000, 15000, size=30)
    
    df = pd.DataFrame({
        'fecha': fechas,
        'ventas': ventas,
        'gastos': ventas * 0.6 + np.random.randint(-1000, 1000, size=30)
    })
    
    # Probar tipos
    fig1 = crear_grafico_temporal(df, 'fecha', 'ventas', "Ventas Diarias", 
                                  tipo='linea', dark_mode=True, area=True)
    fig1.savefig('/mnt/agents/output/test_linea_temporal.png', dpi=150, bbox_inches='tight')
    cerrar_figura(fig1)
    
    fig2 = crear_grafico_lineas_multiples(df, 'fecha', ['ventas', 'gastos'], 
                                          "Ventas vs Gastos", dark_mode=True, paleta='ocean')
    fig2.savefig('/mnt/agents/output/test_multiples.png', dpi=150, bbox_inches='tight')
    cerrar_figura(fig2)
    
    fig3 = crear_grafico_barras_temporal(df, 'fecha', 'ventas', "Ventas Mensuales", 
                                         agrupar='M', dark_mode=True)
    fig3.savefig('/mnt/agents/output/test_barras_temporal.png', dpi=150, bbox_inches='tight')
    cerrar_figura(fig3)
    
    print("✅ Gráficos temporales generados en /mnt/agents/output/")