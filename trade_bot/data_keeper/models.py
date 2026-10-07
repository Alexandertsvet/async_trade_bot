from django.db import models


class FinancialInstrument(models.Model):
    """Модель финансового инструмента на основе данных T-Invest API."""

    # Идентификаторы
    uid = models.UUIDField(
        primary_key=True,
        help_text="Уникальный идентификатор инструмента (Tinkoff UID)",
    )
    figi = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
        help_text="Financial Instrument Global Identifier",
    )
    ticker = models.CharField(
        max_length=20, db_index=True, help_text="Тикер инструмента"
    )
    class_code = models.CharField(
        max_length=20, help_text="Класс-код (например, TQBR)"
    )

    # Описание
    name = models.CharField(
        max_length=255, help_text="Название компании или инструмента"
    )
    type = models.CharField(
        max_length=50,
        help_text="Тип инструмента (shares, etf, bond, currency, futures)",
    )
    exchange = models.CharField(
        max_length=100, help_text="Биржа проведения торгов"
    )
    currency = models.CharField(
        max_length=10, help_text="Валюта торгов (rub, usd, eur...)"
    )

    # Торговые параметры
    lot = models.PositiveIntegerField(help_text="Размер торгового лота")
    min_price_increment = models.DecimalField(
        max_digits=18,
        decimal_places=9,
        help_text="Минимальный шаг цены",
    )
    scale = models.IntegerField(
        help_text="Количество знаков после запятой для цены"
    )
    trading_status = models.CharField(
        max_length=100, help_text="Текущий статус торговли инструментом"
    )

    # Флаги доступности
    api_trade_available_flag = models.BooleanField(
        default=False, help_text="Доступность торговли через API"
    )
    buy_available_flag = models.BooleanField(
        default=False, help_text="Доступность покупки"
    )
    sell_available_flag = models.BooleanField(
        default=False, help_text="Доступность продажи"
    )
    short_enabled_flag = models.BooleanField(
        default=False, help_text="Доступность шорта"
    )

    # Рисковые коэффициенты (маржинальная торговля — разрешаем пустые значения)
    klong = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        blank=True,
        null=True,
        help_text="Коэффициент ставки риска для лонга",
    )
    kshort = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        blank=True,
        null=True,
        help_text="Коэффициент ставки риска для шорта",
    )

    # Системные поля Django
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financial_instruments"
        verbose_name = "Финансовый инструмент"
        verbose_name_plural = "Финансовые инструменты"
        indexes = [
            models.Index(fields=["ticker", "type"]),
        ]

    def __str__(self):
        return f"{self.ticker} - {self.name}"
