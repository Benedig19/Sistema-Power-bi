from database.conexion import conectar

def guardar_datos(df):
    conexion = conectar()
    cursor = conexion.cursor()

    for _, row in df.iterrows():
        sql = "INSERT INTO ventas (producto, ventas) VALUES (%s, %s)"
        valores = (row["producto"], row["ventas"])
        cursor.execute(sql, valores)

    conexion.commit()
    conexion.close()