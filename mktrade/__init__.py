from os import environ, path, makedirs, urandom
from hashlib import sha1
from contextlib import suppress
from flask import Flask, request, session, abort
from werkzeug.security import safe_str_cmp
from .database import db
from . import keystore, terminal


def create_application() -> Flask:
    """
    Функция-фабрика, создающая объект-приложение

    :return: Объект-приложение
    """
    app = Flask(__name__, instance_relative_config=True)
    db_file = path.join(app.instance_path, 'mktrade.sqlite')
    app.config.from_mapping(SECRET_KEY='dev',
                            SQLALCHEMY_DATABASE_URI='sqlite:///{0}'.format(db_file),
                            SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            CSRF_FORM_NAME='csrf_token',
                            CSRF_SESSION_NAME='csrf_token')
    if environ.get('DEBUG', 0):
        app.config.from_mapping(ENV='development', DEBUG=True)

    with suppress(OSError):
        makedirs(app.instance_path)

    db.init_app(app)

    if not path.exists(db_file):
        db.create_all(app=app)

    app.register_blueprint(keystore.bp)
    app.register_blueprint(terminal.bp)
    app.add_url_rule('/', endpoint='keystore.auth')

    @app.context_processor
    def csrf_protection_generator() -> dict:
        if app.config['CSRF_SESSION_NAME'] not in session:
            session[app.config['CSRF_SESSION_NAME']] = sha1(urandom(64)).hexdigest()
        return {app.config['CSRF_FORM_NAME']: session[app.config['CSRF_SESSION_NAME']]}

    @app.before_request
    def csrf_protection_validator() -> None:
        if request.method == 'POST':
            token = session.get(app.config['CSRF_SESSION_NAME'], None)
            if not token or not safe_str_cmp(token, request.form.get(app.config['CSRF_FORM_NAME'], '')):
                abort(403)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    return app
