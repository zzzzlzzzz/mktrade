from functools import wraps
from hashlib import md5
from flask import Blueprint, request, render_template, session, url_for, redirect, flash, abort
from ccxt import exchanges
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from .database import db, Account
from .encryption import Encryption


bp = Blueprint('keystore', __name__, url_prefix='/keystore')


@bp.route('/auth', methods=('GET', 'POST'))
def auth():
    """
    Метод, вызывающийся для получения пароля шифрования от пользователя

    :return: Response
    """
    if request.method == 'POST':
        password = request.form.get('pass')
        if not password or len(password) < 10:
            flash('Password length less that 10 symbols')
        else:
            session['password'] = md5(password.encode('utf8')).hexdigest()[4:28]
            return redirect(url_for('terminal.index'))
    return render_template('keystore/auth.html')


def password_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'password' not in session:
            return redirect(url_for('keystore.auth'))
        return func(*args, **kwargs)
    return wrapper


def keys_process(to_update=None):
    """
    Обработчик формы добавления изменения

    :param to_update: Аккаунт для изменения
    :return: None
    """
    tag = request.form.get('tag')
    exchange = request.form.get('exchange')
    api_key = request.form.get('api_key')
    api_secret = request.form.get('api_secret')
    uid = request.form.get('uid', '')
    password = request.form.get('pass', '')
    try:
        timeout = int(request.form.get('timeout'))
    except ValueError:
        timeout = None
    try:
        nonce_as_time = bool(request.form.get('nonce_as_time'))
    except ValueError:
        nonce_as_time = None

    if not tag:
        flash('Enter account tag')
    elif not exchange or exchange not in exchanges:
        flash('Select exchange')
    elif not api_key or not api_secret:
        flash('Enter api key and api secret both')
    elif timeout is None:
        flash('Enter correct timeout')
    elif nonce_as_time is None:
        flash('Enter correct nonce as time')
    else:
        cipher = Encryption(session['password'])
        api_key = cipher.encrypt(api_key)
        api_secret = cipher.encrypt(api_secret)
        uid = cipher.encrypt(uid)
        password = cipher.encrypt(password)

        if to_update:
            to_update.account_tag = tag
            to_update.exchange_id = exchange
            to_update.api_key = api_key
            to_update.api_secret = api_secret
            to_update.uid = uid
            to_update.password = password
            to_update.exchange_timeout = timeout
            to_update.nonce_as_time = nonce_as_time
            flash('Account updated')
        else:
            db.session.add(Account(tag, exchange, api_key, api_secret, uid, password, timeout, nonce_as_time))
            flash('Account added')
        db.session.commit()


@bp.route('/', methods=('GET', 'POST'))
@password_required
def keys():
    """
    Метод вызывается для добавления нового аккаунта

    :return: Response
    """
    if request.method == 'POST':
        keys_process()

    accounts = Account.query.all()
    return render_template('keystore/keys.html', accounts=accounts, exchanges=exchanges)


@bp.route('/<int:key_id>', methods=('GET', 'POST'))
@password_required
def keys_by_id(key_id):
    """
    Метод вызывается для изменения существующего аккаунта

    :param key_id: ИД существующего аккаунта
    :return: Response
    """
    current_account = None
    try:
        current_account = Account.query.filter_by(account_id=key_id).one()
    except (NoResultFound, MultipleResultsFound):
        abort(404)

    if request.method == 'POST':
        act = request.form.get('act')
        if act == 'add':
            keys_process(current_account)
        elif act == 'del':
            db.session.delete(current_account)
            db.session.commit()
            return redirect(url_for('keystore.keys'))
        else:
            abort(404)

    cipher = Encryption(session['password'])

    current_account_encoded = {
        'account_id': current_account.account_id,
        'account_tag': current_account.account_tag,
        'exchange_id': current_account.exchange_id,
        'api_key': cipher.decrypt(current_account.api_key),
        'api_secret': cipher.decrypt(current_account.api_secret),
        'uid': cipher.decrypt(current_account.uid),
        'password': cipher.decrypt(current_account.password),
        'exchange_timeout': current_account.exchange_timeout,
        'nonce_as_time': current_account.nonce_as_time
    }

    accounts = Account.query.all()
    return render_template('keystore/keys.html', accounts=accounts, current_account=current_account_encoded, exchanges=exchanges)
