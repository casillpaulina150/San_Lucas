from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datos.consultas_auth import actualizar_password_usuario
from datos.consultas_auth import actualizar_password_usuario
from datos.consultas_medico import (
    obtener_citas_del_medico,
    obtener_detalle_cita,
    obtener_lista_expedientes,
    guardar_consulta_completa,
    obtener_expediente_completo,
    eliminar_expediente,
    medico_tiene_acceso_expediente,
    obtener_usuario_medico,
    horario_ya_ocupado,
    crear_cita_seguimiento,
    actualizar_requiere_seguimiento
)

medico = Blueprint("medico", __name__)


def acceso_medico():
    return session.get("rol") == "medico" and session.get("id_usuario") is not None

def obtener_id_medico_sesion():
    return session.get("id_doctor")

def validar_password_confirmacion(usuario, password_recibida):
    password_guardada = usuario.get("contrasena", "")

    if not password_guardada:
        return False, False

    try:
        if check_password_hash(password_guardada, password_recibida):
            return True, False
    except ValueError:
        pass

    # Compatibilidad temporal por si todavía hay contraseñas viejas en texto plano
    if password_guardada == password_recibida:
        return True, True

    return False, False


@medico.route("/dashboard")
def dashboard():
    if not acceso_medico():
        return redirect(url_for("auth.login"))

    id_doctor = obtener_id_medico_sesion()
    if not id_doctor:
        session.clear()
        flash("Tu usuario médico no tiene un doctor asociado.", "danger")
        return redirect(url_for("auth.login"))
    

    citas = obtener_citas_del_medico(id_doctor, "proximas")

    return render_template(
        "dashboard.html",
        citas=citas,
        nombre=session.get("nombre", "Doctor"),
        filtro="proximas"
    )


@medico.route("/panel_medico")
def panel_medico():
    return redirect(url_for("medico.dashboard"))


@medico.route("/detalle_cita/<int:id_cita>", methods=["GET", "POST"])
def detalle_cita(id_cita):
    if not acceso_medico():
        return redirect(url_for("auth.login"))

    id_doctor = obtener_id_medico_sesion()
    if not id_doctor:
        session.clear()
        flash("Tu usuario médico no tiene un doctor asociado.", "danger")
        return redirect(url_for("auth.login"))

    cita = obtener_detalle_cita(id_cita, id_doctor)
    if not cita:
        flash("No se encontró la cita o no tienes acceso a ella.", "danger")
        return redirect(url_for("medico.dashboard"))

    if request.method == "POST":
        datos_generales = {
            "peso": request.form.get("peso"),
            "talla": request.form.get("talla"),
            "presion_arterial": request.form.get("presion_arterial"),
            "temperatura": request.form.get("temperatura"),
            "sangre": request.form.get("sangre"),
            "alergias": request.form.get("alergias"),
            "medicamentos_actuales": request.form.get("medicamentos_actuales"),
            "antecedentes": request.form.get("antecedentes"),
        }

        datos_consulta = {
            "diagnostico": request.form.get("diagnostico"),
            "tratamiento": request.form.get("tratamiento"),
            "observaciones": request.form.get("observaciones"),
        }

        datos_especialidad = {
            "semanas_gestacion": request.form.get("semanas_gestacion"),
            "fum": request.form.get("fum"),
            "gestas": request.form.get("gestas"),
            "partos": request.form.get("partos"),
            "cesareas": request.form.get("cesareas"),
            "abortos": request.form.get("abortos"),
            "frecuencia_cardiaca_fetal": request.form.get("frecuencia_cardiaca_fetal"),
            "movimientos_fetales": request.form.get("movimientos_fetales"),
            "observaciones_obstetricia": request.form.get("observaciones_obstetricia"),
            "tipo_lesion": request.form.get("tipo_lesion"),
            "ubicacion_lesion": request.form.get("ubicacion_lesion"),
            "tiempo_evolucion": request.form.get("tiempo_evolucion"),
            "sintomas_asociados": request.form.get("sintomas_asociados"),
            "tratamiento_topico": request.form.get("tratamiento_topico"),
            "observaciones_dermatologia": request.form.get("observaciones_dermatologia"),
            "imc": request.form.get("imc"),
            "habitos_alimenticios": request.form.get("habitos_alimenticios"),
            "consumo_agua": request.form.get("consumo_agua"),
            "objetivo_nutricional": request.form.get("objetivo_nutricional"),
            "plan_alimenticio": request.form.get("plan_alimenticio"),
            "observaciones_nutricion": request.form.get("observaciones_nutricion"),
            "motivo_psicologico": request.form.get("motivo_psicologico"),
            "estado_emocional": request.form.get("estado_emocional"),
            "evaluacion_mental": request.form.get("evaluacion_mental"),
            "plan_terapeutico": request.form.get("plan_terapeutico"),
            "observaciones_psicologia": request.form.get("observaciones_psicologia"),
        }

        requiere_seguimiento = request.form.get("requiere_seguimiento") == "1"
        fecha_seguimiento = request.form.get("fecha_seguimiento")
        hora_seguimiento = request.form.get("hora_seguimiento")
        motivo_seguimiento = request.form.get("motivo_seguimiento", "").strip()

        guardar_consulta_completa(cita, datos_generales, datos_consulta, datos_especialidad)
        actualizar_requiere_seguimiento(cita["id_cita"], requiere_seguimiento)

        if requiere_seguimiento:
            if not fecha_seguimiento or not hora_seguimiento or not motivo_seguimiento:
                flash("Marcaste seguimiento, pero faltan fecha, hora o motivo de la siguiente cita.", "warning")
                return redirect(url_for("medico.detalle_cita", id_cita=id_cita))

            if horario_ya_ocupado(cita["id_doctor"], fecha_seguimiento, hora_seguimiento):
                flash("La hora seleccionada para el seguimiento ya está ocupada.", "danger")
                return redirect(url_for("medico.detalle_cita", id_cita=id_cita))

            creada, folio_nuevo, error_seguimiento = crear_cita_seguimiento(
                    id_paciente=cita["id_paciente"],
                    id_doctor=cita["id_doctor"],
                    fecha=fecha_seguimiento,
                    hora=hora_seguimiento,
                    motivo=motivo_seguimiento,
                    id_cita_origen=cita["id_cita"]
                )

            if creada:
                    flash(f"La consulta fue guardada y se agendó la cita de seguimiento con folio {folio_nuevo}.", "success")
            else:
                    flash(f"La consulta se guardó, pero no se pudo crear la cita de seguimiento. Error: {error_seguimiento}", "warning")
        else:
            flash("Consulta guardada y cita marcada como atendida.", "success")

        return redirect(url_for("medico.expediente_paciente", id_paciente=cita["id_paciente"]))

    return render_template("detalle_cita.html", cita=cita)


@medico.route("/expediente/verificar/<int:id_paciente>", methods=["GET", "POST"])
def verificar_acceso_expediente(id_paciente):
    if not acceso_medico():
        return redirect(url_for("auth.login"))

    id_doctor = session.get("id_doctor")
    id_usuario = session.get("id_usuario")

    if not id_doctor or not id_usuario:
        return redirect(url_for("auth.login"))

    if not medico_tiene_acceso_expediente(id_doctor, id_paciente):
        flash("Este doctor no tiene permisos para acceder a este expediente.", "error")
        return redirect(url_for("medico.expedientes"))

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        usuario = obtener_usuario_medico(id_usuario)

        if not usuario:
            flash("No se pudo validar el usuario.", "error")
            return redirect(url_for("medico.expedientes"))

        password_valida, migrar_a_hash = validar_password_confirmacion(usuario, password)

        if password_valida:
            if migrar_a_hash:
                nuevo_hash = generate_password_hash(password)
                actualizar_password_usuario(id_usuario, nuevo_hash)

            session[f"acceso_expediente_{id_paciente}"] = True
            return redirect(url_for("medico.expediente_paciente", id_paciente=id_paciente))

        flash("La contraseña es incorrecta.", "error")
        return render_template("confirmar_acceso_expediente.html", id_paciente=id_paciente)

    return render_template("confirmar_acceso_expediente.html", id_paciente=id_paciente)

@medico.route("/expedientes")
def expedientes():
    if not acceso_medico():
        return redirect(url_for("auth.login"))

    id_doctor = obtener_id_medico_sesion()
    if not id_doctor:
        session.clear()
        flash("Tu usuario médico no tiene un doctor asociado.", "danger")
        return redirect(url_for("auth.login"))

    busqueda = request.args.get("q", "").strip()
    expedientes = obtener_lista_expedientes(id_doctor, busqueda)
    return render_template("expedientes.html", expedientes=expedientes)

@medico.route("/expediente/<int:id_paciente>")
def expediente_paciente(id_paciente):
    if not acceso_medico():
        return redirect(url_for("auth.login"))

    id_doctor = session.get("id_doctor")

    if not id_doctor:
        return redirect(url_for("auth.login"))

    if not medico_tiene_acceso_expediente(id_doctor, id_paciente):
        flash("Este doctor no tiene permisos para acceder a este expediente.", "error")
        return redirect(url_for("medico.expedientes"))

    if not session.get(f"acceso_expediente_{id_paciente}"):
        return redirect(url_for("medico.verificar_acceso_expediente", id_paciente=id_paciente))

    paciente, historial = obtener_expediente_completo(id_paciente)

    session.pop(f"acceso_expediente_{id_paciente}", None)

    return render_template(
        "expediente_paciente.html",
        paciente=paciente,
        historial=historial
    )


@medico.route("/expediente/eliminar/<int:id_paciente>", methods=["POST"])
def eliminar_expediente_paciente(id_paciente):
    if not acceso_medico():
        return redirect(url_for("auth.login"))

    flash(
        "La eliminación física de expedientes fue deshabilitada por seguridad. "
        "Si quieres, después hacemos baja lógica.",
        "warning"
    )
    return redirect(url_for("medico.expedientes"))