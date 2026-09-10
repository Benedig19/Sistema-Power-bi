from database.conexion import conectar
import logging


def guardar_en_bd(resultado, nombre_archivo="excel"):

    conexion = None
    cursor = None

    try:
        conexion = conectar()
        cursor = conexion.cursor()

        registros_insertados = 0

        for item in resultado.get("analisis", []):

            top = item.get("top")

            if isinstance(top, dict):

                for clave, valor in top.items():

                    cursor.execute("""
                        INSERT INTO registros (archivo, columna, valor, cantidad)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            cantidad = cantidad + VALUES(cantidad)
                    """, (
                        nombre_archivo,
                        item.get("columna", "sin_columna"),
                        str(clave),
                        int(valor)
                    ))

                    registros_insertados += 1

        conexion.commit()

        print(f"✅ Guardado en MySQL ({registros_insertados} registros) - Archivo: {nombre_archivo}")

    except Exception as e:
        print("❌ Error al guardar en MySQL:", e)

        # guardar en log si usas logging
        logging.error(f"Error MySQL: {e}")

        if conexion:
            conexion.rollback()

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()