from flask_sqlalchemy import SQLAlchemy
import ccxt
from .encryption import Encryption


db = SQLAlchemy()


class Account(db.Model):
    __tablename__ = 'account'

    account_id = db.Column(db.Integer, primary_key=True)
    account_tag = db.Column(db.String(64), nullable=False)
    exchange_id = db.Column(db.String(64), nullable=False)
    api_key = db.Column(db.String(256), nullable=False)
    api_secret = db.Column(db.String(256), nullable=False)
    uid = db.Column(db.String(256), default='')
    password = db.Column(db.String(256), default='')
    exchange_timeout = db.Column(db.Integer(), default=10000)
    nonce_as_time = db.Column(db.Boolean(), default=False)
    nonce = db.Column(db.Integer(), default=1)

    def __init__(self, tag, exchange, key, secret, uid, password, timeout, nonceast):
        self.account_tag = tag
        self.exchange_id = exchange
        self.api_key = key
        self.api_secret = secret
        self.uid = uid
        self.password = password
        self.exchange_timeout = timeout
        self.nonce_as_time = nonceast

    def get_client(self, password):
        """
        Выполняет получение клиента из данных аутентификации

        :param password: Пароль для защиты
        :return: Клиент криптобиржи
        """

        def nonce():
            if self.nonce_as_time:
                return ccxt.Exchange.milliseconds()
            last_nonce = self.nonce
            self.nonce = Account.nonce + 1
            db.session.commit()
            return last_nonce

        client_cls = getattr(ccxt, self.exchange_id, None)
        if not client_cls:
            return None

        cipher = Encryption(password)
        client_settings = {'timeout': self.exchange_timeout,
                           'apiKey': cipher.decrypt(self.api_key),
                           'secret': cipher.decrypt(self.api_secret),
                           'nonce': nonce}
        if self.password:
            client_settings.update({'password': cipher.decrypt(self.password)})
        if self.uid:
            client_settings.update({'uid': cipher.decrypt(self.uid)})

        return client_cls(client_settings)
