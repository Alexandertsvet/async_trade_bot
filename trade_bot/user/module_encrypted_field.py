import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)

class CustomEncryptedCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(settings, 'FIELD_ENCRYPTION_KEY'):
            raise ValueError("Не задан ключ шифрования FIELD_ENCRYPTION_KEY в settings.py")
        self.fernet = Fernet(settings.FIELD_ENCRYPTION_KEY)

    def get_prep_value(self, value):
        """
        Превращает значение в строку и шифрует перед сохранением в базу данных.
        """
        value = super().get_prep_value(value)
        if value:
            return self.fernet.encrypt(value.encode('utf-8')).decode('utf-8')
        return value

    def get_db_prep_save(self, value, connection):
        """
        ГАРАНТИРУЕТ шифрование перед записью/сохранением в базу данных.
        """
        if value:
            value = str(value)
            return self.fernet.encrypt(value.encode('utf-8')).decode('utf-8')
        return super().get_db_prep_save(value, connection)

    def from_db_value(self, value, expression, connection, **kwargs):
        """
        Дешифрует значение при извлечении из базы данных.
        """
        if value:
            try:
                return self.fernet.decrypt(value.encode('utf-8')).decode('utf-8')
            except InvalidToken:
                logger.critical("Критическая ошибка дешифрования поля! Данные повреждены или изменены.")
                raise InvalidToken("Попытка чтения нешифрованных или поврежденных данных!")
        return value

    def contribute_to_class(self, cls, name):
        """
        Добавляет поле в модель и проверяет длину строки.
        """
        super().contribute_to_class(cls, name)
        if self.max_length is None:
            raise ValueError("Длина строки для CustomEncryptedCharField должна быть задана")
