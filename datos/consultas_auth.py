from datos.conexion import obtener_conexion


def obtener_usuario_por_correo(correo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT id_usuario, correo, contrasena, rol, id_doctor, activo
        FROM usuarios
        WHERE correo = %s
        LIMIT 1
    """
    cursor.execute(sql, (correo,))
    usuario = cursor.fetchone()

    cursor.close()
    conexion.close()
    return usuario


def actualizar_password_usuario(id_usuario, nuevo_hash):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        sql = """
            UPDATE usuarios
            SET contrasena = %s
            WHERE id_usuario = %s
        """
        cursor.execute(sql, (nuevo_hash, id_usuario))
        conexion.commit()
        return True
    except Exception as e:
        conexion.rollback()
        print("Error al actualizar password del usuario:", e)
        return False
    finally:
        cursor.close()
        conexion.close()