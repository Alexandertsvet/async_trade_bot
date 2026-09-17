# В Django 6.1 для асинхронности мы импортируем утилиту sync_to_async,
# так как clean() пока не умеет быть async нативно
import logging

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from user.constant import MAX_LENGTH_EMAIL, MAX_LENGTH_USERS
from user.module_encrypted_field import CustomEncryptedCharField

logger = logging.getLogger(__name__)


class User(AbstractUser):
    """
    Модель пользователя для Django проекта (Синглтон).
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
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def clean(self):
        """
        Синхронный метод валидации при создании или обновлении (например, в админке).
        """
        if not self.pk and User.objects.exists():
            logger.critical("Попытка добавить нового пользователя в систему.")
            raise ValidationError(
                "В этой системе может существовать только один пользователь."
            )
        super().clean()

    async def aclean(self):
        """
        Родной асинхронный метод валидации для Django 5.x/6.x.
        Вызывается автоматически внутри afull_clean().
        """
        # Используем родной асинхронный менеджер .aexists()
        if not self.pk and await User.objects.aexists():
            logger.critical(
                "Попытка добавить нового пользователя в систему (async)."
            )
            raise ValidationError(
                "В этой системе может существовать только один пользователь."
            )

        # Вызываем асинхронный super().aclean(), который появился в новых Django
        await super().aclean()

    def save(self, *args, **kwargs):
        """
        Синхронное сохранение (для синхронного контекста).
        """
        self.full_clean()
        super().save(*args, **kwargs)

    async def asave(self, *args, **kwargs):
        """
        Правильное асинхронное сохранение.
        Использует встроенный afull_clean(), который под капотом вызовет наш aclean().
        """
        # ВАЖНО: Никаких sync_to_async(full_clean). Используем нативный метод:
        await self.afull_clean()
        await super().asave(*args, **kwargs)

    def __str__(self):
        return self.username


from t_tech.invest import (
    AccessLevel as TTechAccessLevel,
    AccountStatus as TTechAccountStatus,
    AccountType as TTechAccountType,
)


class TInvestAccount(models.Model):
    """Реальные торговые аккаунты.
    Токен с доступом к конкретному счету — токен
    для получения доступа только к одному конкретному счету пользователя.
    Уровень прав доступа (без права осуществлять переводы между счетами).
    Необходимо в .env
    INVEST_TOKEN=ваш api key
    FIELD_ENCRYPTION_KEY=
    для генерации ключа (FIELD_ENCRYPTION_KEY) использовать команду
    python3 manage.py generate_key
    Пример вывода
    MYwwSOQNqTzqk-XseEgYMQf0G8-9c6mlFC4Eq8aKC4k=
    Ключь успешно создан!
    """

    class AccountType(models.IntegerChoices):
        ACCOUNT_TYPE_UNSPECIFIED = (
            TTechAccountType.ACCOUNT_TYPE_UNSPECIFIED.value,
            "Тип аккаунта не определен.",
        )
        ACCOUNT_TYPE_TINKOFF = (
            TTechAccountType.ACCOUNT_TYPE_TINKOFF.value,
            "Брокерский счет Т-Инвестиций.",
        )
        ACCOUNT_TYPE_TINKOFF_IIS = (
            TTechAccountType.ACCOUNT_TYPE_TINKOFF_IIS.value,
            "ИИС.",
        )
        ACCOUNT_TYPE_INVEST_BOX = (
            TTechAccountType.ACCOUNT_TYPE_INVEST_BOX.value,
            "Инвесткопилка.",
        )
        ACCOUNT_TYPE_INVEST_FUND = (
            TTechAccountType.ACCOUNT_TYPE_INVEST_FUND.value,
            "Фонд денежного рынка.",
        )
        ACCOUNT_TYPE_DEBIT = (
            TTechAccountType.ACCOUNT_TYPE_DEBIT.value,
            "Дебетовый карточный счeт.",
        )
        ACCOUNT_TYPE_SAVING = (
            TTechAccountType.ACCOUNT_TYPE_SAVING.value,
            "Накопительный счeт.",
        )
        ACCOUNT_TYPE_DFA = (
            TTechAccountType.ACCOUNT_TYPE_DFA.value,
            "Смарт-счет.",
        )

    class AccountStatus(models.IntegerChoices):
        ACCOUNT_STATUS_UNSPECIFIED = (
            TTechAccountStatus.ACCOUNT_STATUS_UNSPECIFIED.value,
            "Статус не определён (обычно ошибка запроса).",
        )
        ACCOUNT_STATUS_NEW = (
            TTechAccountStatus.ACCOUNT_STATUS_NEW.value,
            "Счёт находится в процессе открытия (заявка отправлена).",
        )
        ACCOUNT_STATUS_OPEN = (
            TTechAccountStatus.ACCOUNT_STATUS_OPEN.value,
            "Открытый и активный счет.",
        )
        ACCOUNT_STATUS_CLOSED = (
            TTechAccountStatus.ACCOUNT_STATUS_CLOSED.value,
            "Закрытый счет.",
        )
        # ACCOUNT_STATUS_ALL = (TTechAccountStatus.ACCOUNT_STATUS_ALL.value, "Все счета.")

    class AccessLevel(models.IntegerChoices):
        ACCOUNT_ACCESS_LEVEL_UNSPECIFIED = (
            TTechAccessLevel.ACCOUNT_ACCESS_LEVEL_UNSPECIFIED.value,
            "Уровень доступа не определен.",
        )
        ACCOUNT_ACCESS_LEVEL_FULL_ACCESS = (
            TTechAccessLevel.ACCOUNT_ACCESS_LEVEL_FULL_ACCESS.value,
            "Полный доступ к счету.",
        )
        ACCOUNT_ACCESS_LEVEL_READ_ONLY = (
            TTechAccessLevel.ACCOUNT_ACCESS_LEVEL_READ_ONLY.value,
            "Доступ с уровнем прав «только чтение».",
        )
        ACCOUNT_ACCESS_LEVEL_NO_ACCESS = (
            TTechAccessLevel.ACCOUNT_ACCESS_LEVEL_NO_ACCESS.value,
            "Доступа нет.",
        )

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="real_accounts",
    )
    account_id = models.CharField(max_length=50, unique=True)
    access_token = CustomEncryptedCharField(
        max_length=512,
        help_text="api key токен с доступом к конкретному счету T инвестиции",
    )
    description = models.CharField(
        max_length=255, blank=True, help_text="Краткое описание..."
    )
    type = models.IntegerField(
        choices=AccountType.choices, default=AccountType.ACCOUNT_TYPE_TINKOFF
    )
    status = models.IntegerField(
        choices=AccountStatus.choices,
        default=AccountStatus.ACCOUNT_STATUS_OPEN,
    )
    access_level = models.IntegerField(
        choices=AccessLevel.choices,
        default=AccessLevel.ACCOUNT_ACCESS_LEVEL_FULL_ACCESS,
    )
    opened_date = models.DateTimeField(blank=True, null=True)
    closed_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "account_id"], name="unique_user_account_id"
            )
        ]

    def __str__(self):
        return f"Account: {self.account_id}"
