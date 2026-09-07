from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-train-firebase-2026'

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
