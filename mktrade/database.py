from flask_sqlalchemy import SQLAlchemy


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
