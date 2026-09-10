import matplotlib.pyplot as plt
import pandas as pd


def grafico_tendencia(df):

    if "date" not in df.columns or "total_revenue" not in df.columns:
        return None

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    trend = df.groupby("date")["total_revenue"].sum()

    fig, ax = plt.subplots(figsize=(6, 4))

    ax.plot(trend.index, trend.values, marker="o")

    ax.set_title("📈 Tendencia de Ventas")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Ventas")

    plt.xticks(rotation=45)

    return fig