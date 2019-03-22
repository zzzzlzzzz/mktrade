from flask import Blueprint, request
from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms.validators import Length


bp = Blueprint('keystore', __name__, url_prefix='/keystore')


@bp.route('/auth', methods=('GET', 'POST'))
def auth():
    """
    Метод, вызывающийся для получения пароля шифрования от пользователя

    :return: Response
    """
    class AuthForm(FlaskForm):
        password = PasswordField('password', [Length(10)])

    if request.method == 'POST':
        pass
    return 'Work'
