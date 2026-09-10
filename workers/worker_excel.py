from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
from database.guardar import guardar_en_bd


class WorkerExcel(QThread):

    progreso = pyqtSignal(int)
    terminado = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, ruta_excel):
        super().__init__()
        self.ruta = ruta_excel

    def run(self):
        try:
            # =========================
            # 📥 CARGAR EXCEL
            # =========================
            df = pd.read_excel(self.ruta)

            self.progreso.emit(30)

            resultado = {
                "analisis": [],
                "kpis": {}
            }

            # =========================
            # 🔥 ANALISIS COLUMNAS
            # =========================
            for i, col in enumerate(df.columns):

                conteo = df[col].value_counts().head(10).to_dict()

                resultado["analisis"].append({
                    "columna": col,
                    "top": conteo
                })

                progreso = 30 + int((i / len(df.columns)) * 60)
                self.progreso.emit(progreso)

            # =========================
            # 💰 KPIs
            # =========================
            resultado["kpis"] = {
                "registros": len(df),
                "tickets_totales": len(df),
                "ventas_totales": df.select_dtypes(include='number').sum().sum()
            }

            self.progreso.emit(100)
            self.terminado.emit(resultado)

        except Exception as e:
            self.error.emit(str(e))