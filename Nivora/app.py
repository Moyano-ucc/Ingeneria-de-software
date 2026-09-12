from flask import Flask
from controllers.aprender_controller import aprender_bp
from controllers.auth_controller import auth_bp

app = Flask(__name__)
app.secret_key = 'nivora_secret_key'

app.register_blueprint(aprender_bp)
app.register_blueprint(auth_bp)

@app.route('/')
def home():
    return "Servidor NIVORA activo. Ve a /login o /aprender"

if __name__ == '__main__':
    app.run(debug=True, port=5000)