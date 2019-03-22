from os import environ, path, makedirs
from contextlib import suppress
from flask import Flask
from .database import db
from . import keystore


def create_application() -> Flask:
    """
    Функция-фабрика, создающая объект-приложение

    :return: Объект-приложение
    """
    app = Flask(__name__, instance_relative_config=True)
    db_file = path.join(app.instance_path, 'mktrade.sqlite')
    app.config.from_mapping(SECRET_KEY='dev',
                            SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_file}',
                            SQLALCHEMY_TRACK_MODIFICATIONS=False)
    if environ.get('DEBUG', 0):
        app.config.from_mapping(ENV='development', DEBUG=True)

    with suppress(OSError):
        makedirs(app.instance_path)

    db.init_app(app)

    if not path.exists(db_file):
        db.create_all(app=app)

    app.register_blueprint(keystore.bp)
    app.add_url_rule('/', endpoint='keystore.auth')

    return app
