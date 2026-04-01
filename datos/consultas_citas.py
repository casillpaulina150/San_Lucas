from datos.conexion import obtener_conexion


def obtener_doctor_por_nombre(nombre_completo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT id_doctor, id_especialidad, nombre, apellido_paterno, apellido_materno
        FROM doctores
    """
    cursor.execute(sql)
    doctores = cursor.fetchall()

    cursor.close()
    conexion.close()

    nombre_limpio = (
        nombre_completo
        .replace("Dra. ", "")
        .replace("Dr. ", "")
        .replace("Lic. ", "")
        .strip()
    )

    for doctor in doctores:
        nombre_bd = f"{doctor['nombre']} {doctor['apellido_paterno']}".strip()
        if nombre_bd.lower() == nombre_limpio.lower():
            return doctor

    return None


def obtener_siguiente_folio():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    sql = """
        SELECT COALESCE(MAX(CAST(SUBSTRING(folio, 5) AS UNSIGNED)), 0)
        FROM citas
    """
    cursor.execute(sql)
    ultimo = cursor.fetchone()[0]
    ultimo = int(ultimo or 0)

    cursor.close()
    conexion.close()

    return f"CSL-{ultimo + 1:04d}"


def obtener_siguiente_expediente(cursor):
    sql = """
        SELECT COALESCE(MAX(CAST(SUBSTRING(numero_expediente, 5) AS UNSIGNED)), 0)
        FROM pacientes
    """
    cursor.execute(sql)
    ultimo = cursor.fetchone()[0]
    ultimo = int(ultimo or 0)

    return f"EXP-{ultimo + 1:04d}"


def obtener_o_crear_paciente(cursor, cita_info):
    sql_buscar = """
        SELECT id_paciente, numero_expediente
        FROM pacientes
        WHERE nombre = %s
          AND apellido_paterno = %s
          AND apellido_materno = %s
          AND sexo = %s
          AND calle = %s
          AND numero = %s
          AND colonia = %s
          AND cp = %s
          AND telefono = %s
          AND correo = %s
        LIMIT 1
    """

    valores = (
        cita_info["nombre"],
        cita_info["apellido_paterno"],
        cita_info["apellido_materno"],
        cita_info["sexo"],
        cita_info["calle"],
        cita_info["numero"],
        cita_info["colonia"],
        cita_info["cp"],
        cita_info["telefono"],
        cita_info["correo"]
    )

    cursor.execute(sql_buscar, valores)
    paciente = cursor.fetchone()

    if paciente:
        return paciente[0], paciente[1]

    numero_expediente = obtener_siguiente_expediente(cursor)

    sql_insertar = """
        INSERT INTO pacientes (
            numero_expediente, nombre, apellido_paterno, apellido_materno, sexo,
            calle, numero, colonia, cp, telefono, correo
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    valores_insert = (
        numero_expediente,
        cita_info["nombre"],
        cita_info["apellido_paterno"],
        cita_info["apellido_materno"],
        cita_info["sexo"],
        cita_info["calle"],
        cita_info["numero"],
        cita_info["colonia"],
        cita_info["cp"],
        cita_info["telefono"],
        cita_info["correo"]
    )

    cursor.execute(sql_insertar, valores_insert)
    return cursor.lastrowid, numero_expediente


def guardar_paciente_y_cita(cita_info):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        id_paciente, numero_expediente = obtener_o_crear_paciente(cursor, cita_info)
        cita_info["numero_expediente"] = numero_expediente

        sql_cita = """
            INSERT INTO citas (
                folio, id_paciente, id_doctor, fecha, hora, motivo
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """

        valores_cita = (
            cita_info["folio"],
            id_paciente,
            cita_info["id_doctor"],
            cita_info["fecha"],
            cita_info["hora"],
            cita_info["motivo"]
        )

        cursor.execute(sql_cita, valores_cita)
        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def obtener_horas_ocupadas(id_doctor, fecha):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    sql = """
        SELECT TIME_FORMAT(hora, '%H:%i') AS hora_formateada
        FROM citas
        WHERE id_doctor = %s AND fecha = %s
    """

    cursor.execute(sql, (id_doctor, fecha))
    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return [fila[0] for fila in resultados]