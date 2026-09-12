from flask import Flask, render_template
from controllers.aprender_controller import aprender_bp
from controllers.auth_controller import auth_bp

app = Flask(__name__)
app.secret_key = 'nivora_secret_key'

# Registro de controladores (Blueprints)
app.register_blueprint(aprender_bp)
app.register_blueprint(auth_bp)

# Ruta de Inicio (Landing Page)
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)