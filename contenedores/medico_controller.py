from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from werkzeug.security import check_password_hash
from datos.consultas_medico import (
    obtener_citas_del_medico,
    obtener_detalle_cita,
    obtener_lista_expedientes,
    guardar_consulta_completa,
    obtener_expediente_completo,
    eliminar_expediente,
    medico_tiene_acceso_expediente,
    obtener_usuario_medico
)

medico = Blueprint("medico", __name__)


def acceso_medico():
    return session.get("rol") == "medico"


def obtener_id_medico_sesion():
    return session.get("id_doctor") or session.get("id_usuario")


@medico.route("/dashboard")
def dashboard():
    if not acceso_medico():
        return redirect(url_for("auth.login"))

    id_doctor = obtener_id_medico_sesion()
    if not id_doctor:
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
        return redirect(url_for("auth.login"))

    cita = obtener_detalle_cita(id_cita, id_doctor)

    if not cita:
        return redirect(url_for("agenda_bp.agenda"))

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

        guardar_consulta_completa(cita, datos_generales, datos_consulta, datos_especialidad)

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

    # 1. Verificar si el médico tiene relación con el paciente
    if not medico_tiene_acceso_expediente(id_doctor, id_paciente):
        flash("Este doctor no tiene permisos para acceder a este expediente.", "error")
        return redirect(url_for("medico.expedientes"))

    # 2. Si manda contraseña, validarla
    if request.method == "POST":
        password = request.form.get("password", "").strip()
        usuario = obtener_usuario_medico(id_usuario)

        if not usuario:
            flash("No se pudo validar el usuario.", "error")
            return redirect(url_for("medico.expedientes"))

        
        if usuario["contrasena"] == password:
            session[f"acceso_expediente_{id_paciente}"] = True
            return redirect(url_for("medico.expediente_paciente", id_paciente=id_paciente))

        flash("La contraseña es incorrecta.", "error")


    return render_template("confirmar_acceso_expediente.html", id_paciente=id_paciente)


@medico.route("/expedientes")
def expedientes():
    busqueda = request.args.get("q", "").strip()
    expedientes = obtener_lista_expedientes(busqueda)
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

    eliminado = eliminar_expediente(id_paciente)

    if eliminado:
        flash("Expediente eliminado correctamente.", "success")
    else:
        flash("No se pudo eliminar el expediente.", "error")

    return redirect(url_for("medico.expedientes"))