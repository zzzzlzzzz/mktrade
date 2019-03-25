from base64 import b64encode, b64decode
from des import DesKey


class Encryption:
    def __init__(self, password):
        """
        Выполняет инициализацию шифрования

        :param password: Пароль для защиты
        """
        self._des = DesKey(password.encode('utf8'))

    def encrypt(self, text) -> str:
        """
        Шифрует строку

        :param text: Строка для шифрования
        :return: base64 результат
        """
        return b64encode(self._des.encrypt(text.encode('utf8'), padding=True)).decode('utf8')

    def decrypt(self, text) -> str:
        """
        Расшифровывает строку

        :param text: Строка для расшифровки
        :return: Результат
        """
        return self._des.decrypt(b64decode(text.encode('utf8')), padding=True).decode('utf8')
