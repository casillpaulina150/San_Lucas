from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash

from datos.consultas_panel import (
    obtener_doctores_panel,
    obtener_pacientes_panel_recepcion,
    obtener_paciente_por_id_panel,
    cuenta_paciente_existe,
    usuario_paciente_existe,
    crear_cuenta_paciente,
    obtener_citas_calendario
)

panel = Blueprint("panel", __name__)


def acceso_panel():
    return session.get("id_usuario") is not None and session.get("rol") != "medico"


def generar_password_temporal(numero_expediente):
    if not numero_expediente:
        return "SL-2026"

    solo_numeros = "".join(filter(str.isdigit, numero_expediente))
    ultimos = solo_numeros[-4:] if solo_numeros else "0000"
    return f"SL-{ultimos}-26"


@panel.route("/panel_citas")
def panel_citas():
    if not acceso_panel():
        return redirect(url_for("auth.login"))

    q = request.args.get("q", "").strip()
    doctores = obtener_doctores_panel()
    pacientes_panel = obtener_pacientes_panel_recepcion(q)

    resumen_panel = {
        "prospectos": sum(1 for p in pacientes_panel if p["total_citas"] == 1),
        "recurrentes": sum(1 for p in pacientes_panel if p["total_citas"] >= 2),
        "activas": sum(1 for p in pacientes_panel if p["estado_cuenta"] == "Cuenta activa")
    }

    return render_template(
        "panel_citas.html",
        doctores=doctores,
        pacientes_panel=pacientes_panel,
        resumen_panel=resumen_panel
    )


@panel.route("/activar_cuenta_paciente/<int:id_paciente>", methods=["POST"])
def activar_cuenta_paciente(id_paciente):
    if not acceso_panel():
        return redirect(url_for("auth.login"))

    paciente = obtener_paciente_por_id_panel(id_paciente)
    if not paciente:
        flash("No se encontró el paciente.", "error")
        return redirect(url_for("panel.panel_citas"))

    if not paciente["correo"] or not paciente["correo"].strip():
        flash("El paciente no tiene correo registrado. No se puede activar la cuenta.", "error")
        return redirect(url_for("panel.panel_citas"))

    if cuenta_paciente_existe(id_paciente):
        flash("Este paciente ya tiene una cuenta creada.", "error")
        return redirect(url_for("panel.panel_citas"))

    usuario = paciente["correo"].strip().lower()
    if usuario_paciente_existe(usuario):
        flash("Ese correo ya está siendo usado como usuario en otra cuenta de paciente.", "error")
        return redirect(url_for("panel.panel_citas"))

    password_temporal = generar_password_temporal(paciente["numero_expediente"])
    password_hash = generate_password_hash(password_temporal)

    creado = crear_cuenta_paciente(id_paciente, usuario, password_hash)

    if creado:
        flash(
            f"Cuenta activada para {paciente['nombre']} {paciente['apellido_paterno']}. "
            f"Usuario: {usuario} | Contraseña temporal: {password_temporal}",
            "success"
        )
    else:
        flash("No se pudo crear la cuenta del paciente.", "error")

    return redirect(url_for("panel.panel_citas"))


@panel.route("/api/citas_calendario")
def api_citas_calendario():
    if not acceso_panel():
        return jsonify({"error": "No autorizado"}), 401

    citas = obtener_citas_calendario()
    eventos = []

    for cita in citas:
        especialidad = cita["especialidad"]

        if especialidad == "Nutriología":
            color = "#2dc653"
        elif especialidad == "Dermatología":
            color = "#f2994a"
        elif especialidad == "Obstetricia":
            color = "#9b51e0"
        elif especialidad == "Psicología":
            color = "#3b82f6"
        else:
            color = "#94a3b8"

        eventos.append({
            "title": f"{cita['hora'][:5]} {cita['paciente']}",
            "start": f"{cita['fecha']}T{cita['hora']}",
            "backgroundColor": color,
            "borderColor": color,
            "textColor": "#ffffff"
        })

    return jsonify(eventos)