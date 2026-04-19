# backend/app.py
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from database import db
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(app)

    db.init_app(app)

    from routes import prompts, tags, health
    app.register_blueprint(health.bp)
    app.register_blueprint(prompts.bp)
    app.register_blueprint(tags.bp)

    # Serve uploaded files
    @app.route("/uploads/<path>")
    def serve_upload(path):
        return send_from_directory(app.config["UPLOAD_FOLDER"], path)

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=3001)