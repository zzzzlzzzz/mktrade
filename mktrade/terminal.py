from flask import Blueprint, redirect, url_for, abort, session, render_template, request
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from ccxt import BaseError
from .keystore import password_required
from .database import Account


bp = Blueprint('terminal', __name__)


@bp.route('/', methods=('GET', ))
@password_required
def index():
    """
    Переадресует на первый аккаунт, либо на хранилище ключей в случае их отсутствия

    :return: Response
    """
    first_account = Account.query.first()
    if first_account:
        return redirect(url_for('terminal.index_by_id', account_id=first_account.account_id))
    else:
        return redirect(url_for('keystore.keys'))


@bp.route('/<int:account_id>', methods=('GET', ))
@bp.route('/<int:account_id>/<path:symbol>', methods=('GET', ))
@password_required
def index_by_id(account_id, symbol=None):
    """
    Отображает терминал

    :param account_id: Идентификатор аккаунта
    :param symbol: Символ для работы
    :return: Response
    """
    current_account = None
    try:
        current_account = Account.query.filter_by(account_id=account_id).one()
    except (NoResultFound, MultipleResultsFound):
        abort(404)
    accounts = Account.query.all()

    client = current_account.get_client(session['password'])
    try:
        client.load_markets()
    except BaseError:
        abort(503)

    return render_template('terminal/index.html', accounts=accounts, current_account=current_account,
                           symbols=client.symbols, current_symbol=symbol,
                           update_interval=current_account.exchange_timeout)


@bp.route('/balance/<int:account_id>', methods=('GET', ))
def balance(account_id):
    """
    Отображает текущие балансы

    :param account_id: Идентификатор аккаунта
    :return: Response
    """
    current_account = None
    try:
        current_account = Account.query.filter_by(account_id=account_id).one()
    except (NoResultFound, MultipleResultsFound):
        abort(404)

    client = current_account.get_client(session['password'])
    balances = None
    try:
        balances = {name: amount for name, amount in client.fetch_balance().get('total', {}).items() if amount > 0}
    except BaseError:
        abort(503)

    return render_template('terminal/balance.html', balances=balances)


@bp.route('/orders/<int:account_id>/<path:symbol>', methods=('GET', ))
def orders(account_id, symbol):
    """
    Отображает открытые ордера

    :param account_id: Идентификатор аккаунта
    :param symbol: Символ для работы
    :return: Response
    """
    current_account = None
    try:
        current_account = Account.query.filter_by(account_id=account_id).one()
    except (NoResultFound, MultipleResultsFound):
        abort(404)

    client = current_account.get_client(session['password'])
    open_orders = None
    try:
        open_orders = client.fetch_open_orders(symbol)
    except BaseError:
        abort(503)
    return render_template('terminal/orders.html', open_orders=open_orders, current_account=current_account, current_symbol=symbol)


@bp.route('/cancel/<int:account_id>/<path:symbol>', methods=('POST', ))
def cancel(account_id, symbol):
    """
    Обработчик отмены ордера

    :param account_id: Идентификатор аккаунта
    :param symbol: Символ для работы
    :return: Response
    """
    order_id = request.form.get('order_id')

    try:
        current_account = Account.query.filter_by(account_id=account_id).one()
    except (NoResultFound, MultipleResultsFound):
        return render_template('terminal/error-msg.html', message='Invalid account')

    client = current_account.get_client(session['password'])
    try:
        client.cancel_order(order_id, symbol)
    except BaseError as e:
        return render_template('terminal/error-msg.html', message=e)
    return render_template('terminal/ok-msg.html', message='Successfully canceled')


@bp.route('/create/<int:account_id>/<path:symbol>', methods=('POST', ))
def create(account_id, symbol):
    """
    Обработчик создания ордера

    :param account_id: Идентификатор аккаунта
    :param symbol: Символ для работы
    :return: Response
    """
    action = request.form.get('act')
    mode = request.form.get('mode')

    try:
        current_account = Account.query.filter_by(account_id=account_id).one()
    except (NoResultFound, MultipleResultsFound):
        return render_template('terminal/error-msg.html', message='Invalid account')

    client = current_account.get_client(session['password'])
    try:
        client.load_markets()
    except BaseError as e:
        return render_template('terminal/error-msg.html', message=e)

    if symbol not in client.symbols:
        return render_template('terminal/error-msg.html', message='Invalid symbol')

    try:
        amount = float(request.form.get('amount').replace(',', '.'))
    except ValueError:
        amount = None
    else:
        amount = client.amount_to_precision(symbol, amount)

    try:
        price = float(request.form.get('price').replace(',', '.'))
    except ValueError:
        price = None
    else:
        price = client.price_to_precision(symbol, price)

    if action == 'buy':
        if mode == 'market':
            if amount:
                try:
                    client.create_market_buy_order(symbol, amount)
                except BaseError as e:
                    return render_template('terminal/error-msg.html', message=e)
            else:
                return render_template('terminal/error-msg.html', message='Invalid amount')
        elif mode == 'limit':
            if amount and price:
                try:
                    client.create_limit_buy_order(symbol, amount, price)
                except BaseError as e:
                    return render_template('terminal/error-msg.html', message=e)
            else:
                return render_template('terminal/error-msg.html', message='Invalid amount or price')
        else:
            return render_template('terminal/error-msg.html', message='Invalid order type')
    elif action == 'sell':
        if mode == 'market':
            if amount:
                try:
                    client.create_market_sell_order(symbol, amount)
                except BaseError as e:
                    return render_template('terminal/error-msg.html', message=e)
            else:
                return render_template('terminal/error-msg.html', message='Invalid amount')
        elif mode == 'limit':
            if amount and price:
                try:
                    client.create_limit_sell_order(symbol, amount, price)
                except BaseError as e:
                    return render_template('terminal/error-msg.html', message=e)
            else:
                return render_template('terminal/error-msg.html', message='Invalid amount or price')
        else:
            return render_template('terminal/error-msg.html', message='Invalid order type')
    else:
        return render_template('terminal/error-msg.html', message='Action invalid')
    return render_template('terminal/ok-msg.html', message='Successfully created')
