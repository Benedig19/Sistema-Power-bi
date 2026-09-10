import pandas as pd


def analizar_datos(df):

    resultado = {
        "analisis": [],
        "kpis": {},
        "ranking": {}
    }

    df = df.copy()

    ventas = 0
    tickets = 0

    # =========================
    # LIMPIEZA GENERAL
    # =========================
    df.columns = [str(c).strip().lower() for c in df.columns]

    for col in df.columns:

        serie = df[col]
        col_lower = col.lower()

        # =========================
        # 🔥 NUMÉRICO REAL
        # =========================
        if pd.api.types.is_numeric_dtype(serie):

            serie = serie.fillna(0)

            total = float(serie.sum())
            promedio = float(serie.mean())

            resultado["analisis"].append({
                "tipo": "numerico",
                "columna": col,
                "total": total,
                "promedio": promedio
            })

            # detectar ventas
            if any(x in col_lower for x in ["revenue", "venta", "monto", "total", "price"]):
                ventas += total

            # detectar tickets (robusto)
            if "ticket" in col_lower or "qty" in col_lower or "cantidad" in col_lower:
                tickets += int(serie.sum())

            continue

        # =========================
        # 🔥 FECHAS REALES (MEJORADO)
        # =========================
        if serie.dtype == "object":

            fechas = pd.to_datetime(serie, errors="coerce")

            if fechas.notna().mean() > 0.7:

                resultado["analisis"].append({
                    "tipo": "fecha",
                    "columna": col,
                    "min": str(fechas.min()),
                    "max": str(fechas.max())
                })

                continue

            # =========================
            # 🔥 CATEGORÍAS (GRÁFICOS)
            # =========================
            top = serie.value_counts().head(10).to_dict()

            if len(top) > 1:

                resultado["analisis"].append({
                    "tipo": "categoria",
                    "columna": col,
                    "top": top
                })

                # =========================
                # 🔥 RANKING AUTOMÁTICO
                # =========================
                if len(top) > 0:
                    resultado["ranking"][col] = top

        # =========================
        # OTROS TIPOS
        # =========================
        else:
            top = serie.value_counts().head(10).to_dict()

            if len(top) > 0:
                resultado["analisis"].append({
                    "tipo": "categoria",
                    "columna": col,
                    "top": top
                })

    # =========================
    # 🔥 KPIs GLOBALES
    # =========================
    resultado["kpis"] = {
        "ventas_totales": float(ventas),
        "tickets_totales": int(tickets),
        "registros": len(df)
    }

    return resultado