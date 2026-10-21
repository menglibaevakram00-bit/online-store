import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask.cli import with_appcontext
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

from .models import db
from .routes import api
from .seed import seed_products


def database_url_from_environment():
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url
    return URL.create(
        "mysql+pymysql",
        username=os.getenv("DB_USER", "store"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "master_nosirov"),
        query={"charset": "utf8mb4"},
    )


def create_app(test_config=None):
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    app = Flask(
        __name__,
        static_folder=str(frontend_dir) if frontend_dir.is_dir() else None,
        static_url_path="",
    )
    app.config.update(
        SQLALCHEMY_DATABASE_URI=database_url_from_environment(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 280},
        MAX_CONTENT_LENGTH=32 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(api)

    if frontend_dir.is_dir():
        @app.get("/")
        def frontend_index():
            return send_from_directory(frontend_dir, "index.html")

    @app.cli.command("init-db")
    @with_appcontext
    def init_db_command():
        db.create_all()
        seed_products()
        app.logger.info("Database schema is ready.")

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Страница не найдена."}), 404

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"error": "Размер запроса превышает допустимый лимит."}), 413

    @app.errorhandler(400)
    def bad_request(_error):
        return jsonify({"error": "Некорректный запрос."}), 400

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        app.logger.exception("Database request failed", exc_info=error)
        return jsonify({"error": "Не удалось выполнить запрос к базе данных."}), 500

    return app
