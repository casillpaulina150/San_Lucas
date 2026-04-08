from datos.conexion import obtener_conexion

try:
    conexion = obtener_conexion()
    print("Conexión exitosa a MySQL")
    conexion.close()
except Exception as e:
    print("Error de conexión:", e)