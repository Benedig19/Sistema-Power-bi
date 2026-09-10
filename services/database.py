import sqlite3
import pandas as pd


class Database:

    def __init__(self, db_name="sistema.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.crear_tabla()

    def crear_tabla(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS analisis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ventas REAL,
            tickets INTEGER,
            registros INTEGER
        )
        """)
        self.conn.commit()

    def guardar_kpis(self, kpis):
        self.cursor.execute("""
        INSERT INTO analisis (ventas, tickets, registros)
        VALUES (?, ?, ?)
        """, (
            kpis.get("ventas_totales", 0),
            kpis.get("tickets_totales", 0),
            kpis.get("registros", 0)
        ))
        self.conn.commit()

    def obtener_historial(self):
        return pd.read_sql("SELECT * FROM analisis", self.conn)