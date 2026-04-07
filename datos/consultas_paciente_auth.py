from datos.conexion import obtener_conexion


def obtener_cuenta_paciente_por_usuario(usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT
            cp.id_cuenta_paciente,
            cp.id_paciente,
            cp.usuario,
            cp.contrasena,
            cp.activo,
            cp.debe_cambiar_password,
            p.nombre,
            p.apellido_paterno,
            p.apellido_materno,
            p.correo,
            p.numero_expediente
        FROM cuentas_paciente cp
        INNER JOIN pacientes p ON cp.id_paciente = p.id_paciente
        WHERE cp.usuario = %s
        LIMIT 1
    """
    cursor.execute(query, (usuario,))
    cuenta = cursor.fetchone()

    cursor.close()
    conexion.close()

    return cuenta


def obtener_cuenta_paciente_por_id(id_cuenta_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT
            cp.id_cuenta_paciente,
            cp.id_paciente,
            cp.usuario,
            cp.contrasena,
            cp.activo,
            cp.debe_cambiar_password,
            p.nombre,
            p.apellido_paterno,
            p.apellido_materno,
            p.correo,
            p.numero_expediente,
            p.telefono,
            p.sexo,
            p.fecha_nacimiento
        FROM cuentas_paciente cp
        INNER JOIN pacientes p ON cp.id_paciente = p.id_paciente
        WHERE cp.id_cuenta_paciente = %s
        LIMIT 1
    """

    cursor.execute(query, (id_cuenta_paciente,))
    cuenta = cursor.fetchone()
    cursor.close()
    conexion.close()
    return cuenta


def actualizar_password_paciente(id_cuenta_paciente, nuevo_hash):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        query = """
            UPDATE cuentas_paciente
            SET contrasena = %s,
                debe_cambiar_password = 0,
                ultimo_acceso = NOW()
            WHERE id_cuenta_paciente = %s
        """
        cursor.execute(query, (nuevo_hash, id_cuenta_paciente))
        conexion.commit()
        return True
    except Exception as e:
        conexion.rollback()
        print("Error al actualizar password paciente:", e)
        return False
    finally:
        cursor.close()
        conexion.close()


def actualizar_ultimo_acceso_paciente(id_cuenta_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        query = """
            UPDATE cuentas_paciente
            SET ultimo_acceso = NOW()
            WHERE id_cuenta_paciente = %s
        """
        cursor.execute(query, (id_cuenta_paciente,))
        conexion.commit()
        return True
    except Exception as e:
        conexion.rollback()
        print("Error al actualizar último acceso:", e)
        return False
    finally:
        cursor.close()
        conexion.close()

def obtener_proximas_citas_paciente(id_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT
            c.id_cita,
            c.folio,
            c.fecha,
            TIME_FORMAT(c.hora, '%H:%i') AS hora,
            c.motivo,
            d.nombre AS doctor_nombre,
            d.apellido_paterno AS doctor_apellido,
            CASE
                WHEN d.id_especialidad = 1 THEN 'Nutriología'
                WHEN d.id_especialidad = 2 THEN 'Dermatología'
                WHEN d.id_especialidad = 3 THEN 'Obstetricia'
                WHEN d.id_especialidad = 4 THEN 'Psicología'
                ELSE 'Sin especialidad'
            END AS especialidad
        FROM citas c
        INNER JOIN doctores d ON c.id_doctor = d.id_doctor
        WHERE c.id_paciente = %s
          AND (
                c.fecha > CURDATE()
                OR (c.fecha = CURDATE() AND c.hora >= CURTIME())
          )
        ORDER BY c.fecha ASC, c.hora ASC
    """
    cursor.execute(query, (id_paciente,))
    citas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return citas


def obtener_resumen_citas_paciente(id_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT
            COUNT(*) AS total_proximas
        FROM citas
        WHERE id_paciente = %s
          AND (
                fecha > CURDATE()
                OR (fecha = CURDATE() AND hora >= CURTIME())
          )
    """
    cursor.execute(query, (id_paciente,))
    resumen = cursor.fetchone()

    cursor.close()
    conexion.close()

    return resumen

def obtener_historial_paciente(id_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT
            c.id_cita,
            c.folio,
            DATE_FORMAT(c.fecha, '%d/%m/%Y') AS fecha,
            TIME_FORMAT(c.hora, '%H:%i') AS hora,
            c.motivo,
            d.nombre AS doctor_nombre,
            d.apellido_paterno AS doctor_apellido,
            CASE
                WHEN d.id_especialidad = 1 THEN 'Nutriología'
                WHEN d.id_especialidad = 2 THEN 'Dermatología'
                WHEN d.id_especialidad = 3 THEN 'Obstetricia'
                WHEN d.id_especialidad = 4 THEN 'Psicología'
                ELSE 'Sin especialidad'
            END AS especialidad,
            cm.id_consulta,
            cm.diagnostico,
            cm.tratamiento,
            cm.observaciones
        FROM consultas_medicas cm
        INNER JOIN citas c ON cm.id_cita = c.id_cita
        INNER JOIN doctores d ON c.id_doctor = d.id_doctor
        WHERE c.id_paciente = %s
        ORDER BY c.fecha DESC, c.hora DESC
    """

    cursor.execute(query, (id_paciente,))
    historial = cursor.fetchall()

    cursor.close()
    conexion.close()
    return historial

def obtener_recetas_paciente(id_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT
            c.id_cita,
            c.folio,
            DATE_FORMAT(c.fecha, '%d/%m/%Y') AS fecha,
            TIME_FORMAT(c.hora, '%H:%i') AS hora,
            c.motivo,
            d.nombre AS doctor_nombre,
            d.apellido_paterno AS doctor_apellido,
            CASE
                WHEN d.id_especialidad = 1 THEN 'Nutriología'
                WHEN d.id_especialidad = 2 THEN 'Dermatología'
                WHEN d.id_especialidad = 3 THEN 'Obstetricia'
                WHEN d.id_especialidad = 4 THEN 'Psicología'
                ELSE 'Sin especialidad'
            END AS especialidad,
            cm.id_consulta,
            cm.diagnostico,
            cm.tratamiento,
            cm.observaciones
        FROM consultas_medicas cm
        INNER JOIN citas c ON cm.id_cita = c.id_cita
        INNER JOIN doctores d ON c.id_doctor = d.id_doctor
        WHERE c.id_paciente = %s
          AND cm.tratamiento IS NOT NULL
          AND TRIM(cm.tratamiento) <> ''
        ORDER BY c.fecha DESC, c.hora DESC
    """

    cursor.execute(query, (id_paciente,))
    recetas = cursor.fetchall()

    cursor.close()
    conexion.close()
    return recetas

def actualizar_fecha_nacimiento_paciente(id_paciente, fecha_nacimiento):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        query = """
            UPDATE pacientes
            SET fecha_nacimiento = %s
            WHERE id_paciente = %s
        """
        cursor.execute(query, (fecha_nacimiento, id_paciente))
        conexion.commit()
        return cursor.rowcount > 0
    except Exception:
        conexion.rollback()
        return False
    finally:
        cursor.close()
        conexion.close()

def cancelar_cita_paciente(id_cita, id_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        query = """
            DELETE FROM citas
            WHERE id_cita = %s
              AND id_paciente = %s
              AND (
                    fecha > CURDATE()
                    OR (fecha = CURDATE() AND hora >= CURTIME())
                  )
        """
        cursor.execute(query, (id_cita, id_paciente))
        conexion.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conexion.rollback()
        print("Error al cancelar cita del paciente:", e)
        return False
    finally:
        cursor.close()
        conexion.close()