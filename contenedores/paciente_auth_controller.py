from datos.consultas_citas import obtener_doctores, registrar_cita_paciente_existente
import calendar
from datos.horarios import HORARIOS_CITA
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from datos.consultas_paciente_auth import (
    obtener_cuenta_paciente_por_usuario,
    obtener_cuenta_paciente_por_id,
    actualizar_password_paciente,
    actualizar_ultimo_acceso_paciente,
    obtener_proximas_citas_paciente,
    obtener_resumen_citas_paciente,
    obtener_historial_paciente,
    obtener_recetas_paciente,
    actualizar_fecha_nacimiento_paciente,
    cancelar_cita_paciente,
    obtener_cita_paciente_por_id,
    reagendar_cita_paciente,
    obtener_horas_ocupadas_para_paciente
)

paciente_auth = Blueprint("paciente_auth", __name__)

MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

DIAS_SEMANA_ES = ["L", "M", "M", "J", "V", "S", "D"]


def construir_calendario_paciente(proximas_citas):
    hoy = date.today()
    calendario = calendar.Calendar(firstweekday=0)  # Lunes

    semanas_crudas = calendario.monthdayscalendar(hoy.year, hoy.month)
    dias_con_cita = set()

    for cita in proximas_citas:
        fecha_cita = cita.get("fecha")

        if isinstance(fecha_cita, datetime):
            fecha_cita = fecha_cita.date()

        elif isinstance(fecha_cita, str):
            formatos = ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S")
            fecha_parseada = None

            for formato in formatos:
                try:
                    fecha_parseada = datetime.strptime(fecha_cita, formato).date()
                    break
                except ValueError:
                    continue

            if not fecha_parseada:
                continue

            fecha_cita = fecha_parseada

        if isinstance(fecha_cita, date):
            if fecha_cita.year == hoy.year and fecha_cita.month == hoy.month:
                dias_con_cita.add(fecha_cita.day)

    semanas = []
    for semana in semanas_crudas:
        fila = []
        for dia in semana:
            fila.append({
                "numero": dia if dia != 0 else "",
                "es_hoy": dia == hoy.day,
                "tiene_cita": dia in dias_con_cita if dia != 0 else False
            })
        semanas.append(fila)

    return {
        "mes": MESES_ES[hoy.month - 1],
        "anio": hoy.year,
        "hoy": hoy.day,
        "dias_semana": DIAS_SEMANA_ES,
        "semanas": semanas
    }

def enriquecer_estado_citas(citas):
    hoy = date.today()
    citas_enriquecidas = []

    for cita in citas:
        cita_nueva = dict(cita)
        fecha_valor = cita.get("fecha")
        fecha_obj = None

        if isinstance(fecha_valor, datetime):
            fecha_obj = fecha_valor.date()
        elif isinstance(fecha_valor, date):
            fecha_obj = fecha_valor
        elif isinstance(fecha_valor, str):
            formatos = ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S")
            for formato in formatos:
                try:
                    fecha_obj = datetime.strptime(fecha_valor, formato).date()
                    break
                except ValueError:
                    continue

        cita_nueva["estado_cita"] = "Próxima"
        cita_nueva["estado_clase"] = "upcoming"
        cita_nueva["texto_estado"] = "Consulta próxima programada."

        if fecha_obj:
            dias = (fecha_obj - hoy).days

            if dias == 0:
                cita_nueva["estado_cita"] = "Hoy"
                cita_nueva["estado_clase"] = "today"
                cita_nueva["texto_estado"] = "Tu cita es hoy."
            elif dias == 1:
                cita_nueva["estado_cita"] = "Mañana"
                cita_nueva["estado_clase"] = "tomorrow"
                cita_nueva["texto_estado"] = "Tu cita es mañana."
            elif dias > 1:
                cita_nueva["estado_cita"] = "Próxima"
                cita_nueva["estado_clase"] = "upcoming"
                cita_nueva["texto_estado"] = f"Faltan {dias} días."
            else:
                cita_nueva["estado_cita"] = "Pendiente"
                cita_nueva["estado_clase"] = "neutral"
                cita_nueva["texto_estado"] = "Consulta registrada."

        citas_enriquecidas.append(cita_nueva)

    return citas_enriquecidas

def paciente_logueado():
    return session.get("rol_paciente") == "paciente"


@paciente_auth.route("/paciente/login", methods=["GET", "POST"])
def login_paciente():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not usuario or not password:
            flash("Ingresa tu usuario y contraseña.", "error")
            return render_template("login_paciente.html")

        cuenta = obtener_cuenta_paciente_por_usuario(usuario)

        if not cuenta:
            flash("No se encontró una cuenta de paciente con esos datos.", "error")
            return render_template("login_paciente.html")

        if int(cuenta["activo"]) != 1:
            flash("Tu cuenta está inactiva. Comunícate con recepción.", "error")
            return render_template("login_paciente.html")

        if not check_password_hash(cuenta["contrasena"], password):
            flash("La contraseña es incorrecta.", "error")
            return render_template("login_paciente.html")

        session["id_cuenta_paciente"] = cuenta["id_cuenta_paciente"]
        session["id_paciente"] = cuenta["id_paciente"]
        session["rol_paciente"] = "paciente"
        session["nombre_paciente"] = f"{cuenta['nombre']} {cuenta['apellido_paterno']}"

        if int(cuenta["debe_cambiar_password"]) == 1:
            flash("Debes cambiar tu contraseña antes de continuar.", "error")
            return redirect(url_for("paciente_auth.cambiar_password_inicial"))

        actualizar_ultimo_acceso_paciente(cuenta["id_cuenta_paciente"])
        return redirect(url_for("paciente_auth.panel_paciente"))

    return render_template("login_paciente.html")


@paciente_auth.route("/paciente/cambiar-password", methods=["GET", "POST"])
def cambiar_password_inicial():
    if not paciente_logueado():
        return redirect(url_for("paciente_auth.login_paciente"))

    id_cuenta_paciente = session.get("id_cuenta_paciente")
    cuenta = obtener_cuenta_paciente_por_id(id_cuenta_paciente)

    if not cuenta:
        session.clear()
        return redirect(url_for("paciente_auth.login_paciente"))

    if request.method == "POST":
        actual = request.form.get("password_actual", "").strip()
        nueva = request.form.get("nueva_password", "").strip()
        confirmar = request.form.get("confirmar_password", "").strip()

        if not actual or not nueva or not confirmar:
            flash("Completa todos los campos.", "error")
            return render_template("cambiar_password_paciente.html", cuenta=cuenta)

        if not check_password_hash(cuenta["contrasena"], actual):
            flash("La contraseña actual no es correcta.", "error")
            return render_template("cambiar_password_paciente.html", cuenta=cuenta)

        if len(nueva) < 8:
            flash("La nueva contraseña debe tener al menos 8 caracteres.", "error")
            return render_template("cambiar_password_paciente.html", cuenta=cuenta)

        if nueva != confirmar:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("cambiar_password_paciente.html", cuenta=cuenta)

        if actual == nueva:
            flash("La nueva contraseña no puede ser igual a la temporal.", "error")
            return render_template("cambiar_password_paciente.html", cuenta=cuenta)

        nuevo_hash = generate_password_hash(nueva)
        actualizado = actualizar_password_paciente(id_cuenta_paciente, nuevo_hash)

        if actualizado:
            session.clear()
            flash("Tu contraseña fue actualizada correctamente. Inicia sesión con tu nueva contraseña.", "success")
            return redirect(url_for("paciente_auth.login_paciente"))

        flash("No se pudo actualizar la contraseña.", "error")

    return render_template("cambiar_password_paciente.html", cuenta=cuenta)


@paciente_auth.route("/paciente/panel")
def panel_paciente():
    if not paciente_logueado():
        return redirect(url_for("paciente_auth.login_paciente"))

    id_cuenta_paciente = session.get("id_cuenta_paciente")
    cuenta = obtener_cuenta_paciente_por_id(id_cuenta_paciente)

    if not cuenta:
        session.clear()
        return redirect(url_for("paciente_auth.login_paciente"))

    if int(cuenta["debe_cambiar_password"]) == 1:
        return redirect(url_for("paciente_auth.cambiar_password_inicial"))

    proximas_citas_raw = obtener_proximas_citas_paciente(cuenta["id_paciente"])
    proximas_citas = enriquecer_estado_citas(proximas_citas_raw)
    resumen_citas = obtener_resumen_citas_paciente(cuenta["id_paciente"])

    historial_paciente = obtener_historial_paciente(cuenta["id_paciente"])
    total_historial = len(historial_paciente)
    ultima_consulta_historial = historial_paciente[0] if historial_paciente else None
    recetas_paciente = obtener_recetas_paciente(cuenta["id_paciente"])
    total_recetas = len(recetas_paciente)
    ultima_receta = recetas_paciente[0] if recetas_paciente else None

    proxima_cita = proximas_citas[0] if proximas_citas else None
    total_proximas = resumen_citas["total_proximas"] if resumen_citas else 0
    calendario_paciente = construir_calendario_paciente(proximas_citas)

    abrir_modal = request.args.get("abrir_modal")
    perfil_actualizado = request.args.get("perfil_actualizado")
    perfil_error = request.args.get("perfil_error")
    fecha_maxima_hoy = date.today().isoformat()
    cita_cancelada = request.args.get("cita_cancelada")
    cita_error = request.args.get("cita_error")

    return render_template(
    "panel_paciente.html",
    cuenta=cuenta,
    proximas_citas=proximas_citas,
    proxima_cita=proxima_cita,
    total_proximas=total_proximas,
    calendario_paciente=calendario_paciente,
    historial_paciente=historial_paciente,
    total_historial=total_historial,
    ultima_consulta_historial=ultima_consulta_historial,
    recetas_paciente=recetas_paciente,
    total_recetas=total_recetas,
    ultima_receta=ultima_receta,
    abrir_modal=abrir_modal,
    perfil_actualizado=perfil_actualizado,
    perfil_error=perfil_error,
    fecha_maxima_hoy=fecha_maxima_hoy,
    cita_cancelada=cita_cancelada,
    cita_error=cita_error,
)

@paciente_auth.route("/paciente/mis-citas")
def mis_citas_paciente():
    if not paciente_logueado():
        return redirect(url_for("paciente_auth.login_paciente"))

    id_cuenta_paciente = session.get("id_cuenta_paciente")
    cuenta = obtener_cuenta_paciente_por_id(id_cuenta_paciente)

    if not cuenta:
        session.clear()
        return redirect(url_for("paciente_auth.login_paciente"))

    if int(cuenta["debe_cambiar_password"]) == 1:
        return redirect(url_for("paciente_auth.cambiar_password_inicial"))

    proximas_citas_raw = obtener_proximas_citas_paciente(cuenta["id_paciente"])
    proximas_citas = enriquecer_estado_citas(proximas_citas_raw)
    resumen_citas = obtener_resumen_citas_paciente(cuenta["id_paciente"])
    total_proximas = resumen_citas["total_proximas"] if resumen_citas else 0

    return render_template(
        "mis_citas_paciente.html",
        cuenta=cuenta,
        proximas_citas=proximas_citas,
        total_proximas=total_proximas
    )

@paciente_auth.route("/paciente/historial")
def historial_paciente():
    if not paciente_logueado():
        return redirect(url_for("paciente_auth.login_paciente"))

    id_cuenta_paciente = session.get("id_cuenta_paciente")
    cuenta = obtener_cuenta_paciente_por_id(id_cuenta_paciente)

    if not cuenta:
        session.clear()
        return redirect(url_for("paciente_auth.login_paciente"))

    if int(cuenta["debe_cambiar_password"]) == 1:
        return redirect(url_for("paciente_auth.cambiar_password_inicial"))

    historial = obtener_historial_paciente(cuenta["id_paciente"])
    total_historial = len(historial)
    ultima_consulta = historial[0] if historial else None

    return render_template(
        "historial_paciente.html",
        cuenta=cuenta,
        historial=historial,
        total_historial=total_historial,
        ultima_consulta=ultima_consulta
    )

@paciente_auth.route("/paciente/recetas")
def recetas_paciente():
    if not paciente_logueado():
        return redirect(url_for("paciente_auth.login_paciente"))

    id_cuenta_paciente = session.get("id_cuenta_paciente")
    cuenta = obtener_cuenta_paciente_por_id(id_cuenta_paciente)

    if not cuenta:
        session.clear()
        return redirect(url_for("paciente_auth.login_paciente"))

    if int(cuenta["debe_cambiar_password"]) == 1:
        return redirect(url_for("paciente_auth.cambiar_password_inicial"))

    recetas = obtener_recetas_paciente(cuenta["id_paciente"])
    total_recetas = len(recetas)
    ultima_receta = recetas[0] if recetas else None

    return render_template(
        "recetas_paciente.html",
        cuenta=cuenta,
        recetas=recetas,
        total_recetas=total_recetas,
        ultima_receta=ultima_receta
    )

@paciente_auth.route("/paciente/guardar-fecha-nacimiento", methods=["POST"])
def guardar_fecha_nacimiento_paciente():
    if not paciente_logueado():
        return redirect(url_for("paciente_auth.login_paciente"))

    id_cuenta_paciente = session.get("id_cuenta_paciente")
    cuenta = obtener_cuenta_paciente_por_id(id_cuenta_paciente)

    if not cuenta:
        session.clear()
        return redirect(url_for("paciente_auth.login_paciente"))

    fecha_nacimiento = request.form.get("fecha_nacimiento", "").strip()

    if not fecha_nacimiento:
        return redirect(url_for(
            "paciente_auth.panel_paciente",
            abrir_modal="perfil",
            perfil_error="1"
        ))

    try:
        fecha_obj = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
    except ValueError:
        return redirect(url_for(
            "paciente_auth.panel_paciente",
            abrir_modal="perfil",
            perfil_error="1"
        ))

    if fecha_obj > date.today():
        return redirect(url_for(
            "paciente_auth.panel_paciente",
            abrir_modal="perfil",
            perfil_error="1"
        ))

    actualizado = actualizar_fecha_nacimiento_paciente(
        cuenta["id_paciente"],
        fecha_nacimiento
    )

    if not actualizado:
        return redirect(url_for(
            "paciente_auth.panel_paciente",
            abrir_modal="perfil",
            perfil_error="1"
        ))

    return redirect(url_for(
        "paciente_auth.panel_paciente",
        abrir_modal="perfil",
        perfil_actualizado="1"
    ))

@paciente_auth.route("/paciente/cancelar-cita/<int:id_cita>", methods=["POST"])
def cancelar_cita_paciente_route(id_cita):
    if not paciente_logueado():
        return redirect(url_for("paciente_auth.login_paciente"))

    id_cuenta_paciente = session.get("id_cuenta_paciente")
    cuenta = obtener_cuenta_paciente_por_id(id_cuenta_paciente)

    if not cuenta:
        session.clear()
        return redirect(url_for("paciente_auth.login_paciente"))

    if int(cuenta["debe_cambiar_password"]) == 1:
        return redirect(url_for("paciente_auth.cambiar_password_inicial"))

    cancelada, mensaje = cancelar_cita_paciente(id_cita, cuenta["id_paciente"])

    if not cancelada:
        return redirect(url_for(
            "paciente_auth.panel_paciente",
            cita_error=mensaje
        ))

    return redirect(url_for(
        "paciente_auth.panel_paciente",
        cita_cancelada="1"
    ))

@paciente_auth.route("/paciente/agendar-cita", methods=["GET", "POST"])
def agendar_cita_paciente():
    if not paciente_logueado():
        return redirect(url_for("paciente_auth.login_paciente"))

    id_cuenta_paciente = session.get("id_cuenta_paciente")
    cuenta = obtener_cuenta_paciente_por_id(id_cuenta_paciente)

    if not cuenta:
        session.clear()
        return redirect(url_for("paciente_auth.login_paciente"))

    doctores = obtener_doctores()
    fecha_minima = (date.today() + timedelta(days=1)).isoformat()

    if request.method == "POST":
        id_doctor = request.form.get("id_doctor")
        fecha = request.form.get("fecha")
        hora = request.form.get("hora")
        motivo = request.form.get("motivo", "").strip()

        if not id_doctor or not fecha or not hora or not motivo:
            flash("Completa todos los campos de la cita.", "error")
            return render_template(
                "agendar_cita_paciente.html",
                cuenta=cuenta,
                doctores=doctores,
                fecha_minima=fecha_minima,
                horarios_cita=HORARIOS_CITA
            )

        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            flash("La fecha seleccionada no es válida.", "error")
            return render_template(
                "agendar_cita_paciente.html",
                cuenta=cuenta,
                doctores=doctores,
                fecha_minima=fecha_minima,
                horarios_cita=HORARIOS_CITA
            )

        if fecha_obj <= date.today():
            flash("No puedes agendar una cita el mismo día. Selecciona una fecha posterior.", "error")
            return render_template(
                "agendar_cita_paciente.html",
                cuenta=cuenta,
                doctores=doctores,
                fecha_minima=fecha_minima,
                horarios_cita=HORARIOS_CITA
            )

        guardada, error_db = registrar_cita_paciente_existente(
            id_paciente=cuenta["id_paciente"],
            id_doctor=int(id_doctor),
            fecha=fecha,
            hora=hora,
            motivo=motivo
        )

        if not guardada:
            flash(error_db or "No se pudo registrar la cita.", "error")
            return render_template(
                "agendar_cita_paciente.html",
                cuenta=cuenta,
                doctores=doctores,
                fecha_minima=fecha_minima,
                horarios_cita=HORARIOS_CITA
            )

        flash("La cita se agendó correctamente.", "success")
        return redirect(url_for("paciente_auth.panel_paciente"))

    return render_template(
        "agendar_cita_paciente.html",
        cuenta=cuenta,
        doctores=doctores,
        fecha_minima=fecha_minima,
        horarios_cita=HORARIOS_CITA
    )

@paciente_auth.route("/paciente/reagendar-cita/<int:id_cita>", methods=["GET", "POST"])
def reagendar_cita_paciente_route(id_cita):
    if not paciente_logueado():
        return redirect(url_for("paciente_auth.login_paciente"))

    id_cuenta_paciente = session.get("id_cuenta_paciente")
    cuenta = obtener_cuenta_paciente_por_id(id_cuenta_paciente)

    if not cuenta:
        session.clear()
        return redirect(url_for("paciente_auth.login_paciente"))

    if int(cuenta["debe_cambiar_password"]) == 1:
        return redirect(url_for("paciente_auth.cambiar_password_inicial"))

    cita = obtener_cita_paciente_por_id(id_cita, cuenta["id_paciente"])

    if not cita:
        flash("La cita no existe o no pertenece a tu cuenta.", "error")
        return redirect(url_for("paciente_auth.mis_citas_paciente"))

    doctores = obtener_doctores()

    if request.method == "POST":
        id_doctor = request.form.get("id_doctor")
        fecha = request.form.get("fecha")
        hora = request.form.get("hora")
        motivo = request.form.get("motivo", "").strip()

        if not id_doctor or not fecha or not hora or not motivo:
            flash("Completa todos los campos para reagendar la cita.", "error")
            return render_template(
                "reagendar_cita_paciente.html",
                cuenta=cuenta,
                cita=cita,
                doctores=doctores,
                fecha_hoy=date.today().isoformat(),
                horarios_cita=HORARIOS_CITA
            )

        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            flash("La fecha no es válida.", "error")
            return render_template(
                "reagendar_cita_paciente.html",
                cuenta=cuenta,
                cita=cita,
                doctores=doctores,
                fecha_hoy=date.today().isoformat(),
                horarios_cita=HORARIOS_CITA
            )

        if fecha_obj < date.today():
            flash("No puedes reagendar una cita a una fecha pasada.", "error")
            return render_template(
                "reagendar_cita_paciente.html",
                cuenta=cuenta,
                cita=cita,
                doctores=doctores,
                fecha_hoy=date.today().isoformat(),
                horarios_cita=HORARIOS_CITA
            )

        actualizada, error_db = reagendar_cita_paciente(
            id_cita=id_cita,
            id_paciente=cuenta["id_paciente"],
            id_doctor=int(id_doctor),
            fecha=fecha,
            hora=hora,
            motivo=motivo
        )

        if not actualizada:
            flash(error_db or "No se pudo reagendar la cita.", "error")
            cita = obtener_cita_paciente_por_id(id_cita, cuenta["id_paciente"])
            return render_template(
                "reagendar_cita_paciente.html",
                cuenta=cuenta,
                cita=cita,
                doctores=doctores,
                fecha_hoy=date.today().isoformat(),
                horarios_cita=HORARIOS_CITA
            )

        flash("La cita se reagendó correctamente.", "success")
        return redirect(url_for("paciente_auth.mis_citas_paciente"))

    return render_template(
        "reagendar_cita_paciente.html",
        cuenta=cuenta,
        cita=cita,
        doctores=doctores,
        fecha_hoy=date.today().isoformat(),
        horarios_cita=HORARIOS_CITA
    )

@paciente_auth.route("/paciente/api/horas-ocupadas")
def api_horas_ocupadas_paciente():
    if not paciente_logueado():
        return jsonify({"ok": False, "horas": []}), 401

    id_doctor = request.args.get("id_doctor", type=int)
    fecha = request.args.get("fecha", "").strip()
    id_cita_excluir = request.args.get("id_cita_excluir", type=int)

    if not id_doctor or not fecha:
        return jsonify({"ok": False, "horas": []}), 400

    horas = obtener_horas_ocupadas_para_paciente(id_doctor, fecha, id_cita_excluir)

    return jsonify({
        "ok": True,
        "horas": horas
    })

@paciente_auth.route("/paciente/logout")
def logout_paciente():
    session.pop("id_cuenta_paciente", None)
    session.pop("id_paciente", None)
    session.pop("rol_paciente", None)
    session.pop("nombre_paciente", None)
    return redirect(url_for("paciente_auth.login_paciente"))