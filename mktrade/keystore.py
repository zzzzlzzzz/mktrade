from functools import wraps
from flask import Blueprint, request, render_template, session, url_for, redirect, flash


bp = Blueprint('keystore', __name__, url_prefix='/keystore')


@bp.route('/auth', methods=('GET', 'POST'))
def auth():
    """
    Метод, вызывающийся для получения пароля шифрования от пользователя

    :return: Response
    """
    if request.method == 'POST':
        password = request.form.get('pass', None)
        error = None
        if not password or len(password) < 10:
            error = 'Password length less that 10 symbols'
        if not error:
            session['password'] = password
            return redirect(url_for('keystore.keys'))
        flash(error)
    return render_template('keystore/auth.html')


def password_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'password' not in session:
            return redirect(url_for('keystore.auth'))
        return func(*args, **kwargs)
    return wrapper


@bp.route('/keys', methods=('GET', 'POST'))
@password_required
def keys():
    return 'keys'
