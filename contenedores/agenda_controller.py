from flask import Blueprint, render_template, jsonify, session
from datetime import datetime, timedelta
from datos.consultas_panel import obtener_doctores_panel, obtener_citas_calendario

agenda_bp = Blueprint('agenda_bp', __name__)

@agenda_bp.route('/agenda')
def agenda():
    doctores = obtener_doctores_panel()
    id_doctor_actual = session.get("id_doctor")
    return render_template(
        'agenda.html',
        doctores=doctores,
        id_doctor_actual=id_doctor_actual
    )

@agenda_bp.route('/api/citas')
def api_citas():
    citas = obtener_citas_calendario()
    eventos = []

    for cita in citas:
        especialidad = cita["especialidad"]

        if especialidad == "Nutriología":
            color = "#27ae60"
        elif especialidad == "Dermatología":
            color = "#f2994a"
        elif especialidad == "Obstetricia":
            color = "#9b51e0"
        elif especialidad == "Psicología":
            color = "#2f80ed"
        else:
            color = "#6c757d"

        inicio = f"{cita['fecha']}T{cita['hora']}"
        dt_inicio = datetime.strptime(inicio, "%Y-%m-%dT%H:%M:%S")
        dt_fin = dt_inicio + timedelta(minutes=60)

        eventos.append({
            "title": f"{cita['paciente']} — {cita['especialidad']}",
            "start": dt_inicio.isoformat(),
            "end": dt_fin.isoformat(),
            "doctor": cita["doctor"],
            "id_doctor": cita["id_doctor"],
            "backgroundColor": color,
            "borderColor": color,
            "textColor": "#ffffff"
        })

    return jsonify(eventos)