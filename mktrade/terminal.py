from flask import Blueprint, redirect, url_for, abort, session, render_template, request, flash
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from ccxt import BaseError
from .keystore import password_required
from .database import Account


bp = Blueprint('terminal', __name__)


@bp.route('/', methods=('GET', ))
@password_required
def index():
    first_account = Account.query.first()
    if first_account:
        return redirect(url_for('terminal.index_by_id', account_id=first_account.account_id))
    else:
        return redirect(url_for('keystore.keys'))


@bp.route('/<int:account_id>', methods=('GET', ))
@bp.route('/<int:account_id>/<path:symbol>', methods=('GET', 'POST'))
@password_required
def index_by_id(account_id, symbol=None):
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

    if request.method == 'POST' and symbol and symbol in client.symbols:
        amount = request.form.get('amount')
        try:
            amount = float(amount.replace(',', '.'))
        except ValueError:
            amount = None
        else:
            amount = client.amount_to_precision(symbol, amount)
        price = request.form.get('price')
        try:
            price = float(price.replace(',', '.'))
        except ValueError:
            price = None
        else:
            price = client.price_to_precision(symbol, price)
        mode = request.form.get('mode')

        action = request.form.get('act')
        if action and action == 'buy':
            if mode and mode == 'market':
                if amount:
                    try:
                        client.create_market_buy_order(symbol, amount)
                    except BaseError as e:
                        flash('Error: {0}'.format(e))
                else:
                    flash('Amount invalid')
            elif mode and mode == 'limit':
                if amount and price:
                    try:
                        client.create_limit_buy_order(symbol, amount, price)
                    except BaseError as e:
                        flash('Error: {0}'.format(e))
                else:
                    flash('Amount and price invalid')
            else:
                flash('Mode invalid')
        elif action and action == 'sell':
            if mode and mode == 'market':
                if amount:
                    try:
                        client.create_market_sell_order(symbol, amount)
                    except BaseError as e:
                        flash('Error: {0}'.format(e))
                else:
                    flash('Amount invalid')
            elif mode and mode == 'limit':
                if amount and price:
                    try:
                        client.create_limit_sell_order(symbol, amount, price)
                    except BaseError as e:
                        flash('Error: {0}'.format(e))
                else:
                    flash('Amount and price invalid')
            else:
                flash('Mode invalid')
        else:
            flash('Action incorrect')
    return render_template('terminal/index.html', accounts=accounts, current_account=current_account, symbols=client.symbols, current_symbol=symbol, update_interval=current_account.exchange_timeout)


@bp.route('/balance/<int:account_id>', methods=('GET', ))
def balance(account_id):
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
