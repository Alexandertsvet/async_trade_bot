# В Django 6.1 для асинхронности мы импортируем утилиту sync_to_async,
# так как clean() пока не умеет быть async нативно
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from user.constant import MAX_LENGTH_EMAIL, MAX_LENGTH_USERS 
from django.conf import settings
from t_tech.invest import (
    OrderDirection as TTechDirection,
    OrderDirection as TTechOrderDirection,
    OrderExecutionReportStatus as TTechStatus,
    OrderType as TTechOrderType,
    PriceType as TTechPriceType,
    TimeInForceType as TTechTimeInForceType,
)
from t_tech.invest.utils import quotation_to_decimal, money_to_decimal
from t_tech.invest.schemas import (
    MoneyValue,
    Quotation,
)
import uuid
import logging

from user.module_encrypted_field import CustomEncryptedCharField



logger = logging.getLogger(__name__)


class User(AbstractUser):
    """
    Модель пользователя для Django проекта.
    """
    email = models.EmailField(
        verbose_name="e-mail",
        unique=True,
        max_length=MAX_LENGTH_EMAIL,
        help_text="Адрес электронной почты пользователя.",
    )
    username = models.CharField(
        unique=True,
        verbose_name="имя пользователя в системе",
        max_length=MAX_LENGTH_USERS,
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
                "В этой системе может существовать только один пользователь.",
                logger.critical("Попытка добавить нового пользователя в систему.")
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

class TInvestAccount(models.Model):
    """Реальные торговые аккаунты.
    Токен с доступом к конкретному счету — токен
    для получения доступа только к одному конкретному счету пользователя.
    Уровень прав доступа (без права осуществлять переводы между счетами).
    """

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="real_accounts",
    )
    account_id = models.CharField(max_length=50, unique=True)
    access_token = CustomEncryptedCharField(
        max_length=255,
        help_text="api key токен с доступом к конкретному счету T инвестиции",
    )
    description = models.CharField(
        max_length=255, blank=True, help_text="Краткое описание..."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Account: {self.account_id}"
