from flask import Flask, render_template
from controllers.aprender_controller import aprender_bp
from controllers.auth_controller import auth_bp
from controllers.practica_controller import practica_bp
from controllers.progreso_controller import progreso_bp

app = Flask(__name__)
app.secret_key = 'nivora_secret_key'

# Registro de controladores MVC
app.register_blueprint(aprender_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(practica_bp)
app.register_blueprint(progreso_bp)


# Ruta principal
@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)