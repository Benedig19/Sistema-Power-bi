import pandas as pd
import re
import warnings

warnings.simplefilter("ignore")


# =========================
# 🧠 DETECTAR ENCABEZADO
# =========================
def detectar_encabezado(df_raw):
    mejor_fila = 0
    mejor_score = 0

    for i in range(min(15, len(df_raw))):
        fila = df_raw.iloc[i].astype(str)

        score = 0
        score += fila.str.contains(r'[a-zA-Z]', regex=True).sum()
        score -= fila.isna().sum()
        score -= fila.str.isnumeric().sum()

        if score > mejor_score:
            mejor_score = score
            mejor_fila = i

    return mejor_fila


# =========================
# 🧼 LIMPIAR COLUMNAS
# =========================
def limpiar_columnas(cols):
    nuevas = []
    for c in cols:
        c = str(c).strip().lower()
        c = re.sub(r'[^\w\s]', '', c)
        c = re.sub(r'\s+', '_', c)
        nuevas.append(c)
    return nuevas


# =========================
# 📥 LEER EXCEL ROBUSTO
# =========================
def leer_excel(ruta):
    try:
        df_raw = pd.read_excel(ruta, header=None)

        fila_header = detectar_encabezado(df_raw)

        df = pd.read_excel(ruta, header=fila_header)

        df.columns = limpiar_columnas(df.columns)

        df = df.loc[:, ~df.columns.str.contains('unnamed', case=False)]
        df = df.dropna(how='all')
        df = df.reset_index(drop=True)

        print("✅ Excel cargado correctamente")
        print("📌 Encabezado fila:", fila_header)
        print("📊 Columnas:", list(df.columns))

        return df

    except Exception as e:
        print("❌ Error al leer Excel:", str(e))
        return pd.DataFrame()