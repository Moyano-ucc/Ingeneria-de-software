from flask import Flask
from controllers.aprender_controller import aprender_bp

app = Flask(__name__)
app.register_blueprint(aprender_bp)

@app.route('/')
def home():
    return "Servidor NIVORA activo. Ve a /aprender"

if __name__ == '__main__':
    app.run(debug=True, port=5000)