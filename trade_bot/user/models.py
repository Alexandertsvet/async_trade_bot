# В Django 6.1 для асинхронности мы импортируем утилиту sync_to_async,
# так как clean() пока не умеет быть async нативно
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from user.constant import MAX_LENGHT_EMAIL, MAX_LENGHT_USERS

import logging
logger = logging.getLogger(__name__)


class User(AbstractUser):
    """
    Модель пользователя для Django проекта.
    """
    email = models.EmailField(
        verbose_name="e-mail",
        unique=True,
        max_length=MAX_LENGHT_EMAIL,
        help_text="Адрес электронной почты пользователя.",
    )
    username = models.CharField(
        unique=True,
        verbose_name="имя пользователя в системе",
        max_length=MAX_LENGHT_USERS,
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+$",
                message="«Нельзя использовать пробел и символы, кроме . @ + - _».",
            ),
        ],
        help_text="Имя пользователя в системе, которое должно соответствовать регулярному выражению.",
    )

    class Meta:
        verbose_name = "Пользователь."
        verbose_name_plural = "Пользователи."

    def clean(self):
        """
        Метод для валидации данных пользователя при создании или обновлении.
        """
        if not self.pk and User.objects.exists():
            raise ValidationError(
                "В этой системе может существовать только один пользователь.",
                logger.critical("Попытка добавить нового пользователя в систему.")
            )
        super().clean()

    async def aclean(self):
        """
        Асинхронный метод для валидации данных пользователя при создании или обновлении.
        """
        # Используем асинхронный метод ORM — aexists()
        if not self.pk and await User.objects.aexists():
            raise ValidationError(
                "В этой системе может существовать только один пользователь."
            )

        # Запускаем базовый clean в безопасном для async потоке
        await sync_to_async(super().clean)()

    def save(self, *args, **kwargs):
        """
        Метод для сохранения пользователя с асинхронной валидацией.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    async def asave(self, *args, **kwargs):
        """
        Асинхронный метод для сохранения пользователя с асинхронной валидацией.
        """
        await self.aclean()
        await super().asave(*args, **kwargs)

    def __str__(self):
        """
        Метод для получения строкового представления пользователя.
        """
        return self.username
