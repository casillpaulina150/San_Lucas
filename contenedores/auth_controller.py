from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from datos.consultas_auth import autenticar_usuario

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo")
        contrasena = request.form.get("contrasena")

        usuario = autenticar_usuario(correo, contrasena)
        
        print("Correo recibido:", correo)
        print("Contraseña recibida:", contrasena)
        print("Usuario encontrado:", usuario)

        if usuario:
            session["rol"] = usuario["rol"]
            session["nombre"] = usuario["correo"]
            session["id_usuario"] = usuario["id_usuario"]
            session["id_doctor"] = usuario["id_doctor"]
        
            if usuario["rol"] == "medico":
                return redirect(url_for("medico.dashboard"))
            else:
                return redirect(url_for("panel.panel_citas"))

        flash("Correo o contraseña incorrectos", "danger")

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