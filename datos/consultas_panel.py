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

from datos.conexion import obtener_conexion

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