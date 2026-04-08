import os
import smtplib

from dotenv import load_dotenv
from flask import Blueprint, render_template, request, jsonify
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from datos.consultas_citas import (
    obtener_doctor_por_nombre,
    obtener_siguiente_folio,
    guardar_paciente_y_cita,
    obtener_horas_ocupadas
)
from datos.consultas_generales import obtener_especialidades, obtener_doctores
from datos.horarios import HORARIOS_CITA

load_dotenv()

cita = Blueprint("cita", __name__)

HORARIOS_DISPONIBLES = HORARIOS_CITA


def enviar_correo_confirmacion(destinatario, cita_info):
    correo_emisor = os.getenv("MAIL_USER")
    contrasena = os.getenv("MAIL_PASSWORD")

    if not correo_emisor or not contrasena:
        raise RuntimeError("Faltan MAIL_USER o MAIL_PASSWORD en el archivo .env")

    asunto = f"Confirmación de cita - Clínica San Lucas - Folio {cita_info['folio']}"
    cuerpo = f"""
Hola {cita_info['nombre']} {cita_info['apellido_paterno']} {cita_info['apellido_materno']},

Tu cita ha sido registrada correctamente.

Folio: {cita_info['folio']}
Número de expediente: {cita_info['numero_expediente']}
Especialidad: {cita_info['especialidad']}
Médico: {cita_info['medico']}
Fecha: {cita_info['fecha']}
Hora: {cita_info['hora']}

Clínica San Lucas
Teléfono: 664 614 54 69
Correo: {correo_emisor}
Dirección: Av. Paseo de los Héroes 10999, Zona Río, Tijuana, B.C., C.P. 22010

Gracias por confiar en nosotros.
"""

    mensaje = MIMEMultipart()
    mensaje["From"] = correo_emisor
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.attach(MIMEText(cuerpo, "plain", "utf-8"))

    servidor = smtplib.SMTP("smtp.gmail.com", 587)
    servidor.starttls()
    servidor.login(correo_emisor, contrasena)
    servidor.sendmail(correo_emisor, destinatario, mensaje.as_string())
    servidor.quit()


@cita.route("/cita", methods=["GET", "POST"])
def agendar_cita():
    mensaje = None
    especialidades = obtener_especialidades()
    doctores = obtener_doctores()

    if request.method == "POST":
        nombre = request.form.get("nombre")
        apellido_paterno = request.form.get("apellido_paterno")
        apellido_materno = request.form.get("apellido_materno")
        sexo = request.form.get("sexo")
        calle = request.form.get("calle")
        numero = request.form.get("numero")
        colonia = request.form.get("colonia")
        cp = request.form.get("cp")
        telefono = request.form.get("telefono")
        correo = request.form.get("correo")
        especialidad = request.form.get("especialidad")
        medico = request.form.get("medico")
        fecha = request.form.get("fecha")
        hora = request.form.get("hora")
        motivo = request.form.get("motivo")

        doctor = obtener_doctor_por_nombre(medico)

        if not doctor:
            mensaje = "No se encontró el médico seleccionado."
            return render_template(
                "cita.html",
                mensaje=mensaje,
                especialidades=especialidades,
                doctores=doctores
            )

        horas_ocupadas = obtener_horas_ocupadas(doctor["id_doctor"], fecha)

        if hora in horas_ocupadas:
            mensaje = "Ese horario ya no está disponible para el médico seleccionado."
            return render_template(
                "cita.html",
                mensaje=mensaje,
                especialidades=especialidades,
                doctores=doctores
            )

        folio = obtener_siguiente_folio()

        cita_info = {
            "folio": folio,
            "nombre": nombre,
            "apellido_paterno": apellido_paterno,
            "apellido_materno": apellido_materno,
            "sexo": sexo,
            "calle": calle,
            "numero": numero,
            "colonia": colonia,
            "cp": cp,
            "telefono": telefono,
            "correo": correo,
            "especialidad": especialidad,
            "medico": medico,
            "fecha": fecha,
            "hora": hora,
            "motivo": motivo,
            "id_doctor": doctor["id_doctor"]
        }

        guardar_paciente_y_cita(cita_info)

        try:
            enviar_correo_confirmacion(correo, cita_info)
        except Exception as e:
            print("No se pudo enviar el correo:", e)

        return render_template("confirmacion_cita.html", cita=cita_info)

    return render_template(
        "cita.html",
        mensaje=mensaje,
        especialidades=especialidades,
        doctores=doctores
    )


@cita.route("/horarios_disponibles", methods=["GET"])
def horarios_disponibles():
    medico = request.args.get("medico")
    fecha = request.args.get("fecha")

    if not medico or not fecha:
        return jsonify([])

    doctor = obtener_doctor_por_nombre(medico)

    if not doctor:
        return jsonify([])

    horas_ocupadas = obtener_horas_ocupadas(doctor["id_doctor"], fecha)
    horas_libres = [hora for hora in HORARIOS_DISPONIBLES if hora not in horas_ocupadas]

    return jsonify(horas_libres)