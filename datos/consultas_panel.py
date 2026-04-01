from datos.conexion import obtener_conexion


def obtener_doctores_panel():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT
            id_doctor,
            nombre,
            apellido_paterno,
            CASE
                WHEN id_especialidad = 1 THEN 'Nutriología'
                WHEN id_especialidad = 2 THEN 'Dermatología'
                WHEN id_especialidad = 3 THEN 'Obstetricia'
                WHEN id_especialidad = 4 THEN 'Psicología'
                ELSE 'Sin especialidad'
            END AS especialidad
        FROM doctores
        ORDER BY id_especialidad, nombre
    """

    cursor.execute(query)
    doctores = cursor.fetchall()

    cursor.close()
    conexion.close()

    return doctores


def obtener_citas_por_doctor_y_filtro(id_doctor, filtro):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    if filtro == "proximas":
        sql = """
            SELECT 
                c.folio,
                c.fecha,
                TIME_FORMAT(c.hora, '%H:%i') AS hora,
                c.motivo,
                p.numero_expediente,
                p.nombre,
                p.apellido_paterno,
                p.apellido_materno,
                p.telefono,
                p.correo
            FROM citas c
            INNER JOIN pacientes p ON c.id_paciente = p.id_paciente
            WHERE c.id_doctor = %s
              AND (c.fecha > CURDATE() OR (c.fecha = CURDATE() AND c.hora >= CURTIME()))
            ORDER BY c.fecha ASC, c.hora ASC
        """
    elif filtro == "pasadas":
        sql = """
            SELECT 
                c.folio,
                c.fecha,
                TIME_FORMAT(c.hora, '%H:%i') AS hora,
                c.motivo,
                p.numero_expediente,
                p.nombre,
                p.apellido_paterno,
                p.apellido_materno,
                p.telefono,
                p.correo
            FROM citas c
            INNER JOIN pacientes p ON c.id_paciente = p.id_paciente
            WHERE c.id_doctor = %s
              AND (c.fecha < CURDATE() OR (c.fecha = CURDATE() AND c.hora < CURTIME()))
            ORDER BY c.fecha DESC, c.hora DESC
        """
    elif filtro == "siguiente_mes":
        sql = """
            SELECT 
                c.folio,
                c.fecha,
                TIME_FORMAT(c.hora, '%H:%i') AS hora,
                c.motivo,
                p.numero_expediente,
                p.nombre,
                p.apellido_paterno,
                p.apellido_materno,
                p.telefono,
                p.correo
            FROM citas c
            INNER JOIN pacientes p ON c.id_paciente = p.id_paciente
            WHERE c.id_doctor = %s
              AND YEAR(c.fecha) = YEAR(DATE_ADD(CURDATE(), INTERVAL 1 MONTH))
              AND MONTH(c.fecha) = MONTH(DATE_ADD(CURDATE(), INTERVAL 1 MONTH))
            ORDER BY c.fecha ASC, c.hora ASC
        """
    else:
        sql = """
            SELECT 
                c.folio,
                c.fecha,
                TIME_FORMAT(c.hora, '%H:%i') AS hora,
                c.motivo,
                p.numero_expediente,
                p.nombre,
                p.apellido_paterno,
                p.apellido_materno,
                p.telefono,
                p.correo
            FROM citas c
            INNER JOIN pacientes p ON c.id_paciente = p.id_paciente
            WHERE c.id_doctor = %s
            ORDER BY c.fecha ASC, c.hora ASC
        """

    cursor.execute(sql, (id_doctor,))
    citas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return citas

def obtener_citas_calendario():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT
            c.id_cita,
            c.id_doctor,
            c.fecha,
            TIME_FORMAT(c.hora, '%H:%i:%s') AS hora,
            CONCAT(d.nombre, ' ', d.apellido_paterno) AS doctor,
            CASE
                WHEN d.id_especialidad = 1 THEN 'Nutriología'
                WHEN d.id_especialidad = 2 THEN 'Dermatología'
                WHEN d.id_especialidad = 3 THEN 'Obstetricia'
                WHEN d.id_especialidad = 4 THEN 'Psicología'
                ELSE 'Sin especialidad'
            END AS especialidad,
            CONCAT(p.nombre, ' ', p.apellido_paterno) AS paciente
        FROM citas c
        INNER JOIN doctores d ON c.id_doctor = d.id_doctor
        INNER JOIN pacientes p ON c.id_paciente = p.id_paciente
        ORDER BY c.fecha, c.hora
    """

    cursor.execute(query)
    citas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return citas

def obtener_pacientes_panel_recepcion(busqueda=""):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT
            p.id_paciente,
            p.numero_expediente,
            p.nombre,
            p.apellido_paterno,
            p.apellido_materno,
            p.correo,
            COUNT(c.id_cita) AS total_citas,
            CASE
                WHEN COUNT(c.id_cita) = 1 THEN 'Prospecto'
                WHEN COUNT(c.id_cita) >= 2 THEN 'Paciente recurrente'
                ELSE 'Sin citas'
            END AS categoria,
            CASE
                WHEN cp.id_cuenta_paciente IS NULL THEN 'Sin cuenta'
                WHEN cp.debe_cambiar_password = 1 THEN 'Pendiente de cambio'
                ELSE 'Cuenta activa'
            END AS estado_cuenta
        FROM pacientes p
        LEFT JOIN citas c
            ON p.id_paciente = c.id_paciente
        LEFT JOIN cuentas_paciente cp
            ON p.id_paciente = cp.id_paciente
        WHERE (
            %s = ''
            OR p.numero_expediente LIKE %s
            OR p.nombre LIKE %s
            OR p.apellido_paterno LIKE %s
            OR p.apellido_materno LIKE %s
            OR p.correo LIKE %s
        )
        GROUP BY
            p.id_paciente,
            p.numero_expediente,
            p.nombre,
            p.apellido_paterno,
            p.apellido_materno,
            p.correo,
            cp.id_cuenta_paciente,
            cp.debe_cambiar_password
        HAVING COUNT(c.id_cita) >= 1
        ORDER BY total_citas DESC, p.nombre ASC, p.apellido_paterno ASC
    """

    like = f"%{busqueda}%"
    cursor.execute(query, (busqueda, like, like, like, like, like))
    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados

def obtener_paciente_por_id_panel(id_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT
            id_paciente,
            nombre,
            apellido_paterno,
            apellido_materno,
            correo,
            numero_expediente
        FROM pacientes
        WHERE id_paciente = %s
        LIMIT 1
    """
    cursor.execute(query, (id_paciente,))
    paciente = cursor.fetchone()

    cursor.close()
    conexion.close()

    return paciente


def cuenta_paciente_existe(id_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT id_cuenta_paciente
        FROM cuentas_paciente
        WHERE id_paciente = %s
        LIMIT 1
    """
    cursor.execute(query, (id_paciente,))
    cuenta = cursor.fetchone()

    cursor.close()
    conexion.close()

    return cuenta is not None


def usuario_paciente_existe(usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT id_cuenta_paciente
        FROM cuentas_paciente
        WHERE usuario = %s
        LIMIT 1
    """
    cursor.execute(query, (usuario,))
    cuenta = cursor.fetchone()

    cursor.close()
    conexion.close()

    return cuenta is not None


def crear_cuenta_paciente(id_paciente, usuario, contrasena_hash):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        query = """
            INSERT INTO cuentas_paciente (
                id_paciente,
                usuario,
                contrasena,
                activo,
                debe_cambiar_password
            ) VALUES (%s, %s, %s, 1, 1)
        """
        cursor.execute(query, (id_paciente, usuario, contrasena_hash))
        conexion.commit()
        return True

    except Exception as e:
        conexion.rollback()
        print("Error al crear cuenta del paciente:", e)
        return False

    finally:
        cursor.close()
        conexion.close()