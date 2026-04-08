import os
from dotenv import load_dotenv
from flask import Flask

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

app.register_blueprint(home)
app.register_blueprint(cita)
app.register_blueprint(panel)
app.register_blueprint(auth)
app.register_blueprint(agenda_bp)
app.register_blueprint(medico)
app.register_blueprint(paciente_auth)

if __name__ == "__main__":
    app.run(debug=True)