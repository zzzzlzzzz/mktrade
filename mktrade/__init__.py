from os import environ
from flask import Flask


def create_application() -> Flask:
    """
    Функция-фабрика, создающая объект-приложение

    :return: Объект-приложение
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY='dev', DATABASE='mktrade.sqlite')
    if environ.get('DEBUG', 0):
        app.config.from_mapping(ENV='development', DEBUG=True)

    @app.route('/')
    def index():
        return 'Hello, World!'

    return app
