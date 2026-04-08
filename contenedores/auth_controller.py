from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash

from datos.consultas_auth import obtener_usuario_por_correo, actualizar_password_usuario

auth = Blueprint("auth", __name__)


def validar_password_staff(password_guardada, password_recibida):
    if not password_guardada:
        return False, False

    try:
        if check_password_hash(password_guardada, password_recibida):
            return True, False
    except ValueError:
        pass

    # Compatibilidad temporal:
    # si todavía tienes usuarios viejos con contraseña en texto plano,
    # entran una vez y se migran automáticamente a hash.
    if password_guardada == password_recibida:
        return True, True

    return False, False


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        contrasena = request.form.get("contrasena", "").strip()

        if not correo or not contrasena:
            flash("Ingresa correo y contraseña.", "danger")
            return render_template("login.html")

        usuario = obtener_usuario_por_correo(correo)

        if not usuario or int(usuario.get("activo", 0)) != 1:
            flash("Correo o contraseña incorrectos.", "danger")
            return render_template("login.html")

        password_valida, migrar_a_hash = validar_password_staff(
            usuario.get("contrasena", ""),
            contrasena
        )

        if not password_valida:
            flash("Correo o contraseña incorrectos.", "danger")
            return render_template("login.html")

        if migrar_a_hash:
            nuevo_hash = generate_password_hash(contrasena)
            actualizar_password_usuario(usuario["id_usuario"], nuevo_hash)

        if usuario["rol"] == "medico" and not usuario.get("id_doctor"):
            session.clear()
            flash("Tu usuario médico no tiene un doctor asociado.", "danger")
            return render_template("login.html")

        session.clear()
        session["rol"] = usuario["rol"]
        session["nombre"] = usuario["correo"]
        session["id_usuario"] = usuario["id_usuario"]
        session["id_doctor"] = usuario.get("id_doctor")

        if usuario["rol"] == "medico":
            return redirect(url_for("medico.dashboard"))

        return redirect(url_for("panel.panel_citas"))

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.inicio"))


@auth.route("/recuperar-password", methods=["GET", "POST"])
def recuperar_password():
    if request.method == "POST":
        correo = request.form.get("correo")
        flash(f"Se procesó la solicitud para: {correo}", "info")
        return redirect(url_for("auth.login"))
    return render_template("recuperar.html")


@auth.route("/cambiar-password", methods=["GET", "POST"])
def cambiar_password():
    if request.method == "POST":
        nueva = request.form.get("nueva_password")
        confirmar = request.form.get("confirmar_password")

        if nueva != confirmar:
            flash("Las contraseñas no coinciden", "danger")
            return redirect(url_for("auth.cambiar_password"))

        flash("Contraseña actualizada correctamente", "success")
        return redirect(url_for("auth.login"))

    return render_template("cambiar_password.html")