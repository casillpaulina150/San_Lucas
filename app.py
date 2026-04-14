import os
from datetime import timedelta  # <--  Para contar el tiempo de la sesion
from dotenv import load_dotenv
from flask import Flask, session  # <-- Se Agrego 'session' a la importación

from contenedores.home_controller import home
from contenedores.cita_controller import cita
from contenedores.panel_controller import panel
from contenedores.auth_controller import auth
from contenedores.agenda_controller import agenda_bp
from contenedores.medico_controller import medico
from contenedores.paciente_auth_controller import paciente_auth

load_dotenv()

app = Flask(__name__, template_folder="vista", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "cambia-esta-clave-en-env")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# =====================================================================
# PARCHE DE SEGURIDAD CLÍNICA (Aqui se evita que se guarde la Caché y que exista un Timeout)
# =====================================================================

# Se definio que la sesión caduca automáticamente a los 10 minutos
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

@app.before_request
def make_session_permanent():
    """ 
    Fuerza a que Flask controle el tiempo de la sesión en el servidor
    sin importar la configuración de pestañas del navegador del usuario.
    """
    session.permanent = True 
    app.permanent_session_lifetime = timedelta(minutes=10)

@app.after_request
def add_header(response):
    """
    Le prohíbe al navegador guardar información sensible en la memoria caché.
    Si el USUARIO (Médico o Paciente) cierra sesión y le da "Atrás", 
    el sistema lo obligará a iniciar sesión otra vez por seguridad.
    """
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# =====================================================================

app.register_blueprint(home)
app.register_blueprint(cita)
app.register_blueprint(panel)
app.register_blueprint(auth)
app.register_blueprint(agenda_bp)
app.register_blueprint(medico)
app.register_blueprint(paciente_auth)

if __name__ == "__main__":
    app.run(debug=True)
