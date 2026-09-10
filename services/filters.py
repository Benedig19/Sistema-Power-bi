import pandas as pd


def aplicar_filtros(df, fecha=None, columna=None, valor=None):

    data = df.copy()

    # =========================
    # FILTRO POR FECHA
    # =========================
    if fecha and "date" in data.columns:
        data = data[data["date"] == fecha]

    # =========================
    # FILTRO POR COLUMNA
    # =========================
    if columna and valor:
        data = data[data[columna] == valor]

    return data