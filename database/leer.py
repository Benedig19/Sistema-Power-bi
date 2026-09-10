"""
📊 leer.py - Modulo de Lectura de Datos para Dashboard PRO
Mejorado con manejo de errores, logging, cache y multiples fuentes de datos
"""

import os
import sys
import json
import csv
import logging
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Union, Any, cast
from dataclasses import dataclass
from functools import lru_cache
from collections.abc import Mapping
import sqlite3

# Configuracion de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# 📦 ESTRUCTURAS DE DATOS
# =============================================================================

@dataclass
class KPIData:
    """Estructura tipada para KPIs."""
    ventas_totales: float = 0.0
    tickets_totales: int = 0
    registros: int = 0
    clientes_totales: int = 0
    productos_vendidos: int = 0
    ticket_promedio: float = 0.0
    conversion: float = 0.0
    crecimiento: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ventas_totales": self.ventas_totales,
            "tickets_totales": self.tickets_totales,
            "registros": self.registros,
            "clientes_totales": self.clientes_totales,
            "productos_vendidos": self.productos_vendidos,
            "ticket_promedio": self.ticket_promedio,
            "conversion": self.conversion,
            "crecimiento": self.crecimiento
        }


@dataclass  
class AnalisisItem:
    """Estructura tipada para cada analisis/columna."""
    columna: str
    top: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "columna": self.columna,
            "top": self.top
        }


@dataclass
class DashboardData:
    """Estructura principal del dashboard."""
    kpis: KPIData
    analisis: List[AnalisisItem]
    fecha_generacion: str = ""
    total_registros: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kpis": self.kpis.to_dict(),
            "analisis": [a.to_dict() for a in self.analisis],
            "fecha_generacion": self.fecha_generacion,
            "total_registros": self.total_registros
        }


# =============================================================================
# 🔌 CONEXION A BASE DE DATOS (MEJORADA)
# =============================================================================

class DatabaseManager:
    """Gestor de conexiones a base de datos con pool y retry."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self._connection = None
        self._max_retries = 3

    def _default_config(self) -> Dict:
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "dashboard_db"),
            "charset": "utf8mb4"
        }

    def conectar(self):
        """Conecta a MySQL/MariaDB con reintentos."""
        import mysql.connector

        for intento in range(self._max_retries):
            try:
                self._connection = mysql.connector.connect(**self.config)
                logger.info(f"✅ Conexion exitosa a {self.config['database']}")
                return self._connection
            except Exception as e:
                logger.error(f"❌ Intento {intento + 1}/{self._max_retries} fallido: {e}")
                if intento == self._max_retries - 1:
                    raise ConnectionError(f"No se pudo conectar a la BD despues de {self._max_retries} intentos")

    def conectar_sqlite(self, ruta_db: str = "datos.db"):
        """Conecta a SQLite (alternativa ligera)."""
        try:
            self._connection = sqlite3.connect(ruta_db)
            self._connection.row_factory = sqlite3.Row
            logger.info(f"✅ Conexion SQLite exitosa: {ruta_db}")
            return self._connection
        except Exception as e:
            logger.error(f"❌ Error conectando SQLite: {e}")
            raise

    def ejecutar(self, query: str, params: tuple = ()) -> List[Dict]:
        """Ejecuta query y retorna resultados como lista de diccionarios."""
        if not self._connection:
            self.conectar()

        connection = self._connection
        if connection is None:
            raise ConnectionError("No hay conexion activa")

        cursor = None
        try:
            if isinstance(connection, sqlite3.Connection):
                cursor = connection.cursor()
            else:
                cursor = connection.cursor(dictionary=True)
            
            cursor.execute(query, params)
            raw = cursor.fetchall()
            # Normalizar resultados a lista de diccionarios
            if isinstance(connection, sqlite3.Connection):
                cols = [c[0] for c in cursor.description] if cursor.description else []
                resultados = [dict(zip(cols, row)) for row in raw]
            else:
                # En otros conectores (p.ej. MySQL Connector/Python) el cursor puede
                # devolver diccionarios; forzamos dict() para asegurar el tipo.
                # Algunos analizadores de tipos reclaman sobrecargas de dict(),
                # así que manejamos el caso cuando ya es dict y cuando es mapeo.
                from typing import Any, Dict, cast

                resultados = [
                    r if isinstance(r, dict) else dict(cast(Dict[str, Any], r))
                    for r in raw
                ]
            logger.info(f"📊 Query ejecutada: {len(resultados)} filas")
            return resultados
        except Exception as e:
            logger.error(f"❌ Error en query: {e}")
            raise
        finally:
            if cursor is not None:
                cursor.close()

    def cerrar(self):
        """Cierra conexion de forma segura."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("🔒 Conexion cerrada")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cerrar()


# =============================================================================
# 📊 LECTOR DE DATOS PRINCIPAL
# =============================================================================

class DataReader:
    """Lector principal de datos para el dashboard."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self._cache = {}
        self._cache_ttl = 300  # 5 minutos

    # -------------------------------------------------------------------------
    # METODO 1: Desde Base de Datos (MySQL/MariaDB)
    # -------------------------------------------------------------------------

    def obtener_datos_desde_mysql(self, 
                                   tabla: str = "registros",
                                   fecha_desde: Optional[str] = None,
                                   fecha_hasta: Optional[str] = None,
                                   limite: int = 10) -> DashboardData:
        """
        Obtiene datos desde MySQL/MariaDB con filtros de fecha.

        Args:
            tabla: Nombre de la tabla
            fecha_desde: Fecha inicial (YYYY-MM-DD)
            fecha_hasta: Fecha final (YYYY-MM-DD)
            limite: Maximo de items por categoria
        """
        try:
            with self.db:
                # Query base
                where_clause = ""
                params = ()

                if fecha_desde and fecha_hasta:
                    where_clause = "WHERE fecha BETWEEN %s AND %s"
                    params = (fecha_desde, fecha_hasta)
                elif fecha_desde:
                    where_clause = "WHERE fecha >= %s"
                    params = (fecha_desde,)
                elif fecha_hasta:
                    where_clause = "WHERE fecha <= %s"
                    params = (fecha_hasta,)

                # Obtener analisis por columna
                query_analisis = f"""
                    SELECT columna, valor, SUM(cantidad) as total
                    FROM {tabla}
                    {where_clause}
                    GROUP BY columna, valor
                    ORDER BY columna, total DESC
                """

                rows = self.db.ejecutar(query_analisis, params)
                analisis = self._procesar_filas_a_analisis(rows, limite)

                # Obtener KPIs
                kpis = self._calcular_kpis_mysql(tabla, where_clause, params)

                # Contar total de registros
                query_count = f"SELECT COUNT(*) as total FROM {tabla} {where_clause}"
                count_result = self.db.ejecutar(query_count, params)
                total_registros = count_result[0]["total"] if count_result else 0

                return DashboardData(
                    kpis=kpis,
                    analisis=analisis,
                    fecha_generacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    total_registros=total_registros
                )

        except Exception as e:
            logger.error(f"❌ Error obteniendo datos MySQL: {e}")
            raise

    def _calcular_kpis_mysql(self, tabla: str, where_clause: str, params: tuple) -> KPIData:
        """Calcula KPIs desde MySQL."""
        queries = {
            "ventas": f"SELECT SUM(cantidad * precio) as total FROM {tabla} {where_clause}",
            "tickets": f"SELECT COUNT(DISTINCT ticket_id) as total FROM {tabla} {where_clause}",
            "registros": f"SELECT COUNT(*) as total FROM {tabla} {where_clause}",
            "clientes": f"SELECT COUNT(DISTINCT cliente_id) as total FROM {tabla} {where_clause}",
            "productos": f"SELECT SUM(cantidad) as total FROM {tabla} {where_clause}"
        }

        resultados = {}
        for key, query in queries.items():
            try:
                res = self.db.ejecutar(query, params)
                resultados[key] = res[0]["total"] if res and res[0]["total"] else 0
            except:
                resultados[key] = 0

        ventas = float(resultados.get("ventas", 0))
        tickets = int(resultados.get("tickets", 1))

        return KPIData(
            ventas_totales=ventas,
            tickets_totales=tickets,
            registros=int(resultados.get("registros", 0)),
            clientes_totales=int(resultados.get("clientes", 0)),
            productos_vendidos=int(resultados.get("productos", 0)),
            ticket_promedio=round(ventas / tickets, 2) if tickets > 0 else 0.0
        )

    # -------------------------------------------------------------------------
    # METODO 2: Desde SQLite
    # -------------------------------------------------------------------------

    def obtener_datos_desde_sqlite(self,
                                    ruta_db: str = "datos.db",
                                    tabla: str = "registros",
                                    fecha_desde: Optional[str] = None,
                                    fecha_hasta: Optional[str] = None,
                                    limite: int = 10) -> DashboardData:
        """Obtiene datos desde SQLite."""
        try:
            self.db.conectar_sqlite(ruta_db)

            where_clause = ""
            params = ()

            if fecha_desde and fecha_hasta:
                where_clause = "WHERE fecha BETWEEN ? AND ?"
                params = (fecha_desde, fecha_hasta)

            conn = self.db._connection
            if conn is None:
                raise ConnectionError("No hay conexion SQLite activa")
            cursor = conn.cursor()

            # Analisis
            query = f"""
                SELECT columna, valor, SUM(cantidad) as total
                FROM {tabla}
                {where_clause}
                GROUP BY columna, valor
                ORDER BY columna, total DESC
            """
            cursor.execute(query, params)
            rows = [dict(cast(Mapping[str, Any], row)) for row in cursor.fetchall()]
            analisis = self._procesar_filas_a_analisis(rows, limite)

            # KPIs
            cursor.execute(f"SELECT COUNT(*) as total FROM {tabla} {where_clause}", params)
            total_row = cursor.fetchone()
            total_registros_valor = None
            if total_row is not None:
                try:
                    if isinstance(total_row, dict):
                        total_registros_valor = total_row.get("total")
                    else:
                        total_registros_valor = total_row[0]
                except Exception:
                    total_registros_valor = None

            # Convert to int robustly from various possible types
            if total_registros_valor is None:
                total_registros = 0
            else:
                try:
                    if isinstance(total_registros_valor, int):
                        total_registros = total_registros_valor
                    elif isinstance(total_registros_valor, float):
                        total_registros = int(total_registros_valor)
                    elif isinstance(total_registros_valor, str):
                        total_registros = int(total_registros_valor.strip())
                    elif isinstance(total_registros_valor, bytes):
                        total_registros = int(total_registros_valor.decode("utf-8").strip())
                    else:
                        total_registros = int(float(str(total_registros_valor)))
                except (TypeError, ValueError):
                    total_registros = 0

            cursor.close()
            self.db.cerrar()

            return DashboardData(
                kpis=KPIData(registros=total_registros),
                analisis=analisis,
                fecha_generacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_registros=total_registros
            )

        except Exception as e:
            logger.error(f"❌ Error SQLite: {e}")
            raise

    # -------------------------------------------------------------------------
    # METODO 3: Desde CSV
    # -------------------------------------------------------------------------

    def obtener_datos_desde_csv(self,
                                 ruta_csv: str,
                                 columna_categoria: str = "categoria",
                                 columna_valor: str = "valor",
                                 columna_cantidad: str = "cantidad",
                                 separador: str = ";") -> DashboardData:
        """
        Lee datos desde archivo CSV.

        Args:
            ruta_csv: Ruta al archivo CSV
            columna_categoria: Nombre de la columna de categorias
            columna_valor: Nombre de la columna de valores/items
            columna_cantidad: Nombre de la columna de cantidades
            separador: Separador del CSV (; o ,)
        """
        try:
            if not os.path.exists(ruta_csv):
                raise FileNotFoundError(f"No existe el archivo: {ruta_csv}")

            logger.info(f"📁 Leyendo CSV: {ruta_csv}")

            datos = {}
            total_registros = 0

            with open(ruta_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=separador)

                for row in reader:
                    total_registros += 1
                    categoria = row.get(columna_categoria, "Sin categoria")
                    item = row.get(columna_valor, "Sin nombre")

                    try:
                        cantidad = float(row.get(columna_cantidad, 0))
                    except ValueError:
                        cantidad = 0

                    if categoria not in datos:
                        datos[categoria] = {}

                    if item in datos[categoria]:
                        datos[categoria][item] += cantidad
                    else:
                        datos[categoria][item] = cantidad

            # Convertir a formato analisis
            analisis = []
            for cat, items in datos.items():
                # Ordenar y limitar a top 10
                items_ordenados = dict(sorted(items.items(), 
                                               key=lambda x: x[1], 
                                               reverse=True)[:10])
                analisis.append(AnalisisItem(columna=cat, top=items_ordenados))

            logger.info(f"✅ CSV procesado: {total_registros} registros, {len(analisis)} categorias")

            return DashboardData(
                kpis=KPIData(registros=total_registros),
                analisis=analisis,
                fecha_generacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_registros=total_registros
            )

        except Exception as e:
            logger.error(f"❌ Error leyendo CSV: {e}")
            raise

    # -------------------------------------------------------------------------
    # METODO 4: Desde JSON
    # -------------------------------------------------------------------------

    def obtener_datos_desde_json(self, ruta_json: str) -> DashboardData:
        """Lee datos desde archivo JSON existente."""
        try:
            if not os.path.exists(ruta_json):
                raise FileNotFoundError(f"No existe: {ruta_json}")

            with open(ruta_json, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Si ya tiene el formato correcto
            if "kpis" in data and "analisis" in data:
                kpis = KPIData(**data.get("kpis", {}))
                analisis = [AnalisisItem(**a) for a in data.get("analisis", [])]
                return DashboardData(
                    kpis=kpis,
                    analisis=analisis,
                    fecha_generacion=data.get("fecha_generacion", ""),
                    total_registros=data.get("total_registros", 0)
                )

            # Si es un JSON plano, convertir
            return self._convertir_json_plano(data)

        except Exception as e:
            logger.error(f"❌ Error leyendo JSON: {e}")
            raise

    # -------------------------------------------------------------------------
    # METODO 5: Datos de ejemplo (fallback)
    # -------------------------------------------------------------------------

    @staticmethod
    def obtener_datos_ejemplo() -> DashboardData:
        """Retorna datos de ejemplo para pruebas."""
        return DashboardData(
            kpis=KPIData(
                ventas_totales=154320.50,
                tickets_totales=3421,
                registros=15000,
                clientes_totales=892,
                productos_vendidos=5234,
                ticket_promedio=45.11,
                conversion=68.5,
                crecimiento=23.4
            ),
            analisis=[
                AnalisisItem("Productos Top", {
                    "Laptop Dell XPS": 45000, "iPhone 15 Pro": 38000,
                    "Monitor 4K LG": 22000, "Teclado Mecanico": 15000,
                    "Mouse Logitech": 12000, "Webcam HD": 8000,
                    "Auriculares Sony": 6000, "Hub USB-C": 4000
                }),
                AnalisisItem("Ciudades", {
                    "Madrid": 52000, "Barcelona": 41000, "Valencia": 28000,
                    "Sevilla": 19000, "Bilbao": 14000, "Malaga": 11000
                }),
                AnalisisItem("Vendedores", {
                    "Carlos Ruiz": 35000, "Ana Martinez": 32000,
                    "Luis Garcia": 28000, "Maria Lopez": 24000,
                    "Pedro Sanchez": 19000, "Laura Torres": 15000
                })
            ],
            fecha_generacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_registros=15000
        )

    # -------------------------------------------------------------------------
    # METODOS AUXILIARES
    # -------------------------------------------------------------------------

    def _procesar_filas_a_analisis(self, rows: List[Dict], limite: int = 10) -> List[AnalisisItem]:
        """Convierte filas de BD al formato de analisis del dashboard."""
        resultado = {}

        for row in rows:
            col = row.get("columna", "Sin categoria")
            val = row.get("valor", "Sin nombre")
            total = float(row.get("total", 0))

            if col not in resultado:
                resultado[col] = {}

            resultado[col][val] = total

        # Ordenar y limitar
        analisis = []
        for col, valores in resultado.items():
            ordenado = dict(sorted(valores.items(), 
                                  key=lambda x: x[1], 
                                  reverse=True)[:limite])
            analisis.append(AnalisisItem(columna=col, top=ordenado))

        return analisis

    def _convertir_json_plano(self, data: Dict) -> DashboardData:
        """Convierte un JSON plano al formato del dashboard."""
        analisis = []
        for key, values in data.items():
            if isinstance(values, dict):
                top = dict(sorted(values.items(), 
                                 key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
                                 reverse=True)[:10])
                analisis.append(AnalisisItem(columna=key, top=top))

        return DashboardData(
            kpis=KPIData(),
            analisis=analisis,
            fecha_generacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_registros=len(analisis)
        )

    def exportar_a_json(self, data: DashboardData, ruta: str = "dashboard_data.json"):
        """Exporta los datos a JSON para cache o transferencia."""
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(data.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Datos exportados a: {ruta}")
        except Exception as e:
            logger.error(f"❌ Error exportando JSON: {e}")


# =============================================================================
# 🚀 FUNCION PRINCIPAL (COMPATIBILIDAD CON TU CODIGO ORIGINAL)
# =============================================================================

def obtener_datos_dashboard(
    fuente: str = "mysql",
    tabla: str = "registros",
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    ruta_archivo: Optional[str] = None,
    limite: int = 10
) -> Dict[str, Any]:
    """
    Funcion principal compatible con tu codigo original.

    Args:
        fuente: "mysql", "sqlite", "csv", "json", "ejemplo"
        tabla: Nombre de la tabla en BD
        fecha_desde: Filtro fecha inicial (YYYY-MM-DD)
        fecha_hasta: Filtro fecha final (YYYY-MM-DD)
        ruta_archivo: Ruta al archivo CSV/JSON/SQLite
        limite: Maximo de items por categoria

    Returns:
        Dict con formato {"kpis": {...}, "analisis": [...]}
    """
    reader = DataReader()

    try:
        if fuente == "mysql":
            data = reader.obtener_datos_desde_mysql(tabla, fecha_desde, fecha_hasta, limite)
        elif fuente == "sqlite":
            data = reader.obtener_datos_desde_sqlite(ruta_archivo or "datos.db", tabla, fecha_desde, fecha_hasta, limite)
        elif fuente == "csv":
            if not ruta_archivo:
                raise ValueError("Debes proporcionar ruta_archivo para CSV")
            data = reader.obtener_datos_desde_csv(ruta_archivo)
        elif fuente == "json":
            if not ruta_archivo:
                raise ValueError("Debes proporcionar ruta_archivo para JSON")
            data = reader.obtener_datos_desde_json(ruta_archivo)
        else:
            data = DataReader.obtener_datos_ejemplo()

        return data.to_dict()

    except Exception as e:
        logger.error(f"❌ Error obteniendo datos: {e}")
        logger.info("🔄 Usando datos de ejemplo como fallback")
        return DataReader.obtener_datos_ejemplo().to_dict()


# =============================================================================
# 📝 EJEMPLOS DE USO
# =============================================================================

if __name__ == "__main__":
    # Ejemplo 1: Desde MySQL con filtros de fecha
    # resultado = obtener_datos_dashboard(
    #     fuente="mysql",
    #     tabla="ventas",
    #     fecha_desde="2024-01-01",
    #     fecha_hasta="2024-12-31"
    # )

    # Ejemplo 2: Desde CSV
    # resultado = obtener_datos_dashboard(
    #     fuente="csv",
    #     ruta_archivo="mis_datos.csv"
    # )

    # Ejemplo 3: Datos de ejemplo (para probar)
    resultado = obtener_datos_dashboard(fuente="ejemplo")

    print(json.dumps(resultado, indent=2, ensure_ascii=False))