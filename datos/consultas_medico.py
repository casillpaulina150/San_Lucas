from datos.conexion import obtener_conexion


def obtener_citas_del_medico(id_doctor, filtro="proximas"):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    if filtro == "proximas":
        sql = """
            SELECT
                c.id_cita,
                c.id_paciente,
                c.folio,
                c.fecha,
                TIME_FORMAT(c.hora, '%H:%i') AS hora,
                c.motivo,
                p.numero_expediente,
                CONCAT(
                    p.nombre, ' ',
                    p.apellido_paterno, ' ',
                    IFNULL(p.apellido_materno, '')
                ) AS paciente,
                e.nombre AS especialidad,
                COALESCE(c.estado_cita, 'programada') AS estado_cita
            FROM citas c
            INNER JOIN pacientes p ON c.id_paciente = p.id_paciente
            INNER JOIN doctores d ON c.id_doctor = d.id_doctor
            INNER JOIN especialidades e ON d.id_especialidad = e.id_especialidad
            WHERE c.id_doctor = %s
              AND (c.fecha > CURDATE() OR (c.fecha = CURDATE() AND c.hora >= CURTIME()))
            ORDER BY c.fecha ASC, c.hora ASC
        """
    elif filtro == "pasadas":
        sql = """
            SELECT
                c.id_cita,
                c.id_paciente,
                c.folio,
                c.fecha,
                TIME_FORMAT(c.hora, '%H:%i') AS hora,
                c.motivo,
                p.numero_expediente,
                CONCAT(
                    p.nombre, ' ',
                    p.apellido_paterno, ' ',
                    IFNULL(p.apellido_materno, '')
                ) AS paciente,
                e.nombre AS especialidad,
                COALESCE(c.estado_cita, 'programada') AS estado_cita
            FROM citas c
            INNER JOIN pacientes p ON c.id_paciente = p.id_paciente
            INNER JOIN doctores d ON c.id_doctor = d.id_doctor
            INNER JOIN especialidades e ON d.id_especialidad = e.id_especialidad
            WHERE c.id_doctor = %s
              AND (c.fecha < CURDATE() OR (c.fecha = CURDATE() AND c.hora < CURTIME()))
            ORDER BY c.fecha DESC, c.hora DESC
        """
    elif filtro == "siguiente_mes":
        sql = """
            SELECT
                c.id_cita,
                c.id_paciente,
                c.folio,
                c.fecha,
                TIME_FORMAT(c.hora, '%H:%i') AS hora,
                c.motivo,
                p.numero_expediente,
                CONCAT(
                    p.nombre, ' ',
                    p.apellido_paterno, ' ',
                    IFNULL(p.apellido_materno, '')
                ) AS paciente,
                e.nombre AS especialidad,
                COALESCE(c.estado_cita, 'programada') AS estado_cita
            FROM citas c
            INNER JOIN pacientes p ON c.id_paciente = p.id_paciente
            INNER JOIN doctores d ON c.id_doctor = d.id_doctor
            INNER JOIN especialidades e ON d.id_especialidad = e.id_especialidad
            WHERE c.id_doctor = %s
              AND YEAR(c.fecha) = YEAR(DATE_ADD(CURDATE(), INTERVAL 1 MONTH))
              AND MONTH(c.fecha) = MONTH(DATE_ADD(CURDATE(), INTERVAL 1 MONTH))
            ORDER BY c.fecha ASC, c.hora ASC
        """
    else:
        sql = """
            SELECT
                c.id_cita,
                c.id_paciente,
                c.folio,
                c.fecha,
                TIME_FORMAT(c.hora, '%H:%i') AS hora,
                c.motivo,
                p.numero_expediente,
                CONCAT(
                    p.nombre, ' ',
                    p.apellido_paterno, ' ',
                    IFNULL(p.apellido_materno, '')
                ) AS paciente,
                e.nombre AS especialidad,
                COALESCE(c.estado_cita, 'programada') AS estado_cita
            FROM citas c
            INNER JOIN pacientes p ON c.id_paciente = p.id_paciente
            INNER JOIN doctores d ON c.id_doctor = d.id_doctor
            INNER JOIN especialidades e ON d.id_especialidad = e.id_especialidad
            WHERE c.id_doctor = %s
            ORDER BY c.fecha ASC, c.hora ASC
        """

    cursor.execute(sql, (id_doctor,))
    citas = cursor.fetchall()

    cursor.close()
    conexion.close()
    return citas


def obtener_detalle_cita(id_cita, id_doctor):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT
            c.id_cita,
            c.folio,
            c.fecha,
            TIME_FORMAT(c.hora, '%H:%i') AS hora,
            c.motivo,
            c.id_doctor,
            p.id_paciente,
            p.numero_expediente,
            p.nombre,
            p.apellido_paterno,
            p.apellido_materno,
            p.sexo,
            p.calle,
            p.numero,
            p.colonia,
            p.cp,
            p.telefono,
            p.correo,
            e.nombre AS especialidad
        FROM citas c
        INNER JOIN pacientes p ON c.id_paciente = p.id_paciente
        INNER JOIN doctores d ON c.id_doctor = d.id_doctor
        INNER JOIN especialidades e ON d.id_especialidad = e.id_especialidad
        WHERE c.id_cita = %s AND c.id_doctor = %s
        LIMIT 1
    """
    cursor.execute(sql, (id_cita, id_doctor))
    cita = cursor.fetchone()

    cursor.close()
    conexion.close()
    return cita


def actualizar_ficha_clinica(id_paciente, datos_generales):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    sql_verificar = """
        SELECT id_ficha
        FROM ficha_clinica_paciente
        WHERE id_paciente = %s
        LIMIT 1
    """
    cursor.execute(sql_verificar, (id_paciente,))
    ficha = cursor.fetchone()

    if ficha:
        sql_update = """
            UPDATE ficha_clinica_paciente
            SET peso = %s,
                talla = %s,
                presion_arterial = %s,
                temperatura = %s,
                sangre = %s,
                alergias = %s,
                medicamentos_actuales = %s,
                antecedentes = %s
            WHERE id_paciente = %s
        """
        valores = (
            datos_generales["peso"],
            datos_generales["talla"],
            datos_generales["presion_arterial"],
            datos_generales["temperatura"],
            datos_generales["sangre"],
            datos_generales["alergias"],
            datos_generales["medicamentos_actuales"],
            datos_generales["antecedentes"],
            id_paciente
        )
        cursor.execute(sql_update, valores)
    else:
        sql_insert = """
            INSERT INTO ficha_clinica_paciente (
                id_paciente, peso, talla, presion_arterial, temperatura,
                sangre, alergias, medicamentos_actuales, antecedentes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            id_paciente,
            datos_generales["peso"],
            datos_generales["talla"],
            datos_generales["presion_arterial"],
            datos_generales["temperatura"],
            datos_generales["sangre"],
            datos_generales["alergias"],
            datos_generales["medicamentos_actuales"],
            datos_generales["antecedentes"]
        )
        cursor.execute(sql_insert, valores)

    conexion.commit()
    cursor.close()
    conexion.close()


def guardar_consulta_completa(cita, datos_generales, datos_consulta, datos_especialidad):
    actualizar_ficha_clinica(cita["id_paciente"], datos_generales)

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    sql_consulta = """
        INSERT INTO consultas_medicas (
            id_cita, diagnostico, tratamiento, observaciones
        )
        VALUES (%s, %s, %s, %s)
    """
    valores_consulta = (
        cita["id_cita"],
        datos_consulta["diagnostico"],
        datos_consulta["tratamiento"],
        datos_consulta["observaciones"]
    )
    cursor.execute(sql_consulta, valores_consulta)
    id_consulta = cursor.lastrowid

    especialidad = cita["especialidad"]

    if especialidad == "Obstetricia":
        sql = """
            INSERT INTO consulta_obstetricia (
                id_consulta, semanas_gestacion, fum, gestas, partos,
                cesareas, abortos, frecuencia_cardiaca_fetal,
                movimientos_fetales, observaciones_obstetricia
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            id_consulta,
            datos_especialidad.get("semanas_gestacion"),
            datos_especialidad.get("fum"),
            datos_especialidad.get("gestas"),
            datos_especialidad.get("partos"),
            datos_especialidad.get("cesareas"),
            datos_especialidad.get("abortos"),
            datos_especialidad.get("frecuencia_cardiaca_fetal"),
            datos_especialidad.get("movimientos_fetales"),
            datos_especialidad.get("observaciones_obstetricia")
        )
        cursor.execute(sql, valores)

    elif especialidad == "Dermatología":
        sql = """
            INSERT INTO consulta_dermatologia (
                id_consulta, tipo_lesion, ubicacion_lesion, tiempo_evolucion,
                sintomas_asociados, tratamiento_topico, observaciones_dermatologia
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            id_consulta,
            datos_especialidad.get("tipo_lesion"),
            datos_especialidad.get("ubicacion_lesion"),
            datos_especialidad.get("tiempo_evolucion"),
            datos_especialidad.get("sintomas_asociados"),
            datos_especialidad.get("tratamiento_topico"),
            datos_especialidad.get("observaciones_dermatologia")
        )
        cursor.execute(sql, valores)

    elif especialidad in ("Nutrición", "Nutriología"):
        sql = """
            INSERT INTO consulta_nutricion (
                id_consulta, imc, habitos_alimenticios, consumo_agua,
                objetivo_nutricional, plan_alimenticio, observaciones_nutricion
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            id_consulta,
            datos_especialidad.get("imc"),
            datos_especialidad.get("habitos_alimenticios"),
            datos_especialidad.get("consumo_agua"),
            datos_especialidad.get("objetivo_nutricional"),
            datos_especialidad.get("plan_alimenticio"),
            datos_especialidad.get("observaciones_nutricion")
        )
        cursor.execute(sql, valores)

    elif especialidad == "Psicología":
        sql = """
            INSERT INTO consulta_psicologia (
                id_consulta, motivo_psicologico, estado_emocional,
                evaluacion_mental, plan_terapeutico, observaciones_psicologia
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        valores = (
            id_consulta,
            datos_especialidad.get("motivo_psicologico"),
            datos_especialidad.get("estado_emocional"),
            datos_especialidad.get("evaluacion_mental"),
            datos_especialidad.get("plan_terapeutico"),
            datos_especialidad.get("observaciones_psicologia")
        )
        cursor.execute(sql, valores)

    try:
        cursor.execute("""
            UPDATE citas
            SET estado_cita = 'atendida'
            WHERE id_cita = %s
        """, (cita["id_cita"],))
    except Exception as e:
        print("Aviso: no se pudo actualizar estado_cita:", e)

    conexion.commit()
    cursor.close()
    conexion.close()


def obtener_expediente_completo(id_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    sql_paciente = """
        SELECT
            p.id_paciente,
            p.numero_expediente,
            p.nombre,
            p.apellido_paterno,
            p.apellido_materno,
            p.sexo,
            p.telefono,
            p.correo,
            p.calle,
            p.numero,
            p.colonia,
            p.cp,
            f.peso,
            f.talla,
            f.presion_arterial,
            f.temperatura,
            f.sangre,
            f.alergias,
            f.medicamentos_actuales,
            f.antecedentes
        FROM pacientes p
        LEFT JOIN ficha_clinica_paciente f ON p.id_paciente = f.id_paciente
        WHERE p.id_paciente = %s
        LIMIT 1
    """
    cursor.execute(sql_paciente, (id_paciente,))
    paciente = cursor.fetchone()

    sql_historial = """
        SELECT
            c.id_cita,
            c.folio,
            c.fecha,
            TIME_FORMAT(c.hora, '%H:%i') AS hora,
            c.motivo,
            d.nombre AS doctor_nombre,
            d.apellido_paterno AS doctor_apellido_paterno,
            e.nombre AS especialidad,
            cm.id_consulta,
            cm.diagnostico,
            cm.tratamiento,
            cm.observaciones,
            co.semanas_gestacion,
            co.fum,
            co.gestas,
            co.partos,
            co.cesareas,
            co.abortos,
            co.frecuencia_cardiaca_fetal,
            co.movimientos_fetales,
            co.observaciones_obstetricia,
            cd.tipo_lesion,
            cd.ubicacion_lesion,
            cd.tiempo_evolucion,
            cd.sintomas_asociados,
            cd.tratamiento_topico,
            cd.observaciones_dermatologia,
            cn.imc,
            cn.habitos_alimenticios,
            cn.consumo_agua,
            cn.objetivo_nutricional,
            cn.plan_alimenticio,
            cn.observaciones_nutricion,
            cp.motivo_psicologico,
            cp.estado_emocional,
            cp.evaluacion_mental,
            cp.plan_terapeutico,
            cp.observaciones_psicologia
        FROM citas c
        INNER JOIN doctores d ON c.id_doctor = d.id_doctor
        INNER JOIN especialidades e ON d.id_especialidad = e.id_especialidad
        LEFT JOIN consultas_medicas cm ON c.id_cita = cm.id_cita
        LEFT JOIN consulta_obstetricia co ON cm.id_consulta = co.id_consulta
        LEFT JOIN consulta_dermatologia cd ON cm.id_consulta = cd.id_consulta
        LEFT JOIN consulta_nutricion cn ON cm.id_consulta = cn.id_consulta
        LEFT JOIN consulta_psicologia cp ON cm.id_consulta = cp.id_consulta
        WHERE c.id_paciente = %s
        ORDER BY c.fecha DESC, c.hora DESC
    """
    cursor.execute(sql_historial, (id_paciente,))
    historial = cursor.fetchall()

    cursor.close()
    conexion.close()
    return paciente, historial


def obtener_lista_expedientes(id_doctor, busqueda=""):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT
            p.id_paciente,
            p.numero_expediente,
            p.nombre,
            p.apellido_paterno,
            p.apellido_materno,
            MIN(CONCAT(c.fecha, ' ', c.hora)) AS primera_modificacion,
            MAX(CONCAT(c.fecha, ' ', c.hora)) AS ultima_modificacion
        FROM pacientes p
        INNER JOIN citas c ON p.id_paciente = c.id_paciente
        WHERE c.id_doctor = %s
          AND (
                %s = ''
                OR p.numero_expediente LIKE %s
                OR p.nombre LIKE %s
                OR p.apellido_paterno LIKE %s
                OR p.apellido_materno LIKE %s
              )
        GROUP BY
            p.id_paciente,
            p.numero_expediente,
            p.nombre,
            p.apellido_paterno,
            p.apellido_materno
        ORDER BY p.numero_expediente ASC
    """

    like = f"%{busqueda}%"
    cursor.execute(query, (id_doctor, busqueda, like, like, like, like))
    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()
    return resultados


def eliminar_expediente(id_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT cm.id_consulta
            FROM consultas_medicas cm
            INNER JOIN citas c ON cm.id_cita = c.id_cita
            WHERE c.id_paciente = %s
        """, (id_paciente,))
        consultas = cursor.fetchall()
        ids_consultas = [c["id_consulta"] for c in consultas]

        if ids_consultas:
            placeholders = ",".join(["%s"] * len(ids_consultas))

            cursor.execute(
                f"DELETE FROM consulta_dermatologia WHERE id_consulta IN ({placeholders})",
                ids_consultas
            )
            cursor.execute(
                f"DELETE FROM consulta_nutricion WHERE id_consulta IN ({placeholders})",
                ids_consultas
            )
            cursor.execute(
                f"DELETE FROM consulta_obstetricia WHERE id_consulta IN ({placeholders})",
                ids_consultas
            )
            cursor.execute(
                f"DELETE FROM consulta_psicologia WHERE id_consulta IN ({placeholders})",
                ids_consultas
            )
            cursor.execute(
                f"DELETE FROM consultas_medicas WHERE id_consulta IN ({placeholders})",
                ids_consultas
            )

        cursor.execute("""
            DELETE FROM ficha_clinica_paciente
            WHERE id_paciente = %s
        """, (id_paciente,))

        cursor.execute("""
            DELETE FROM citas
            WHERE id_paciente = %s
        """, (id_paciente,))

        cursor.execute("""
            DELETE FROM pacientes
            WHERE id_paciente = %s
        """, (id_paciente,))

        conexion.commit()
        return True

    except Exception as e:
        conexion.rollback()
        print("Error al eliminar expediente:", e)
        return False

    finally:
        cursor.close()
        conexion.close()


def medico_tiene_acceso_expediente(id_doctor, id_paciente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT 1
        FROM citas
        WHERE id_doctor = %s AND id_paciente = %s
        LIMIT 1
    """
    cursor.execute(sql, (id_doctor, id_paciente))
    resultado = cursor.fetchone()

    cursor.close()
    conexion.close()
    return resultado is not None


def obtener_usuario_medico(id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT id_usuario, correo, contrasena, rol, id_doctor, activo
        FROM usuarios
        WHERE id_usuario = %s
        LIMIT 1
    """
    cursor.execute(sql, (id_usuario,))
    usuario = cursor.fetchone()

    cursor.close()
    conexion.close()
    return usuario


def horario_ya_ocupado(id_doctor, fecha, hora):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        sql = """
            SELECT COUNT(*)
            FROM citas
            WHERE id_doctor = %s
              AND fecha = %s
              AND hora = %s
              AND COALESCE(estado_cita, 'programada') IN ('programada', 'atendida')
        """
        cursor.execute(sql, (id_doctor, fecha, hora))
        total = cursor.fetchone()[0]
        return total > 0
    finally:
        cursor.close()
        conexion.close()


def obtener_siguiente_folio_seguimiento():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTRING(folio, 5) AS UNSIGNED)), 0)
            FROM citas
            WHERE folio LIKE 'CSL-%'
        """)
        resultado = cursor.fetchone()
        ultimo = int(resultado[0]) if resultado and resultado[0] is not None else 0

        siguiente = ultimo + 1
        folio = "CSL-" + str(siguiente).zfill(4)

        print("ULTIMO FOLIO:", ultimo)
        print("NUEVO FOLIO:", folio)

        return folio

    except Exception as e:
        print("Error al generar folio de seguimiento:", e)
        raise

    finally:
        cursor.close()
        conexion.close()


def crear_cita_seguimiento(id_paciente, id_doctor, fecha, hora, motivo, id_cita_origen):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        folio = obtener_siguiente_folio_seguimiento()

        print("=== DEBUG CITA SEGUIMIENTO ===")
        print("folio:", folio)
        print("id_paciente:", id_paciente)
        print("id_doctor:", id_doctor)
        print("fecha:", fecha)
        print("hora:", hora)
        print("motivo:", motivo)
        print("id_cita_origen:", id_cita_origen)

        sql = """
            INSERT INTO citas (
                folio,
                id_paciente,
                id_doctor,
                fecha,
                hora,
                motivo,
                estado_cita,
                requiere_seguimiento,
                id_cita_origen,
                tipo_cita
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        valores = (
            folio,
            int(id_paciente),
            int(id_doctor),
            fecha,
            hora,
            motivo,
            "programada",
            0,
            int(id_cita_origen),
            "seguimiento"
        )

        cursor.execute(sql, valores)
        conexion.commit()

        print("CITA DE SEGUIMIENTO CREADA OK")
        return True, folio, None

    except Exception as e:
        conexion.rollback()
        print("ERROR REAL AL CREAR CITA DE SEGUIMIENTO:", e)
        return False, None, str(e)

    finally:
        cursor.close()
        conexion.close()


def actualizar_requiere_seguimiento(id_cita, requiere_seguimiento):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        sql = """
            UPDATE citas
            SET requiere_seguimiento = %s
            WHERE id_cita = %s
        """
        cursor.execute(sql, (1 if requiere_seguimiento else 0, id_cita))
        conexion.commit()
        return True

    except Exception as e:
        conexion.rollback()
        print("Error al actualizar requiere_seguimiento:", e)
        return False

    finally:
        cursor.close()
        conexion.close()