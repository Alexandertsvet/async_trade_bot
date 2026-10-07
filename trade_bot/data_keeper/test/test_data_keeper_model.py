import uuid
from decimal import Decimal

import pytest
from django.db.utils import IntegrityError

from data_keeper.models import FinancialInstrument


@pytest.fixture
def valid_instrument_data():
    """Фикстура с валидными тестовыми данными для финансового инструмента."""
    return {
        "uid": uuid.uuid4(),
        "figi": "BBG004730N88",
        "ticker": "SBER",
        "class_code": "TQBR",
        "name": "Сбербанк России",
        "type": "shares",
        "exchange": "MOEX",
        "currency": "rub",
        "lot": 10,
        "min_price_increment": Decimal("0.010000000"),
        "scale": 2,
        "trading_status": "NORMAL_TRADING",
        "api_trade_available_flag": True,
        "buy_available_flag": True,
        "sell_available_flag": True,
        "short_enabled_flag": True,
        "klong": Decimal("0.15000000"),
        "kshort": Decimal("0.20000000"),
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestFinancialInstrumentModelAsync:
    """
    Набор асинхронных тестов для контроля целостности модели FinancialInstrument.
    """

    async def test_create_instrument_success(self, valid_instrument_data):
        """
        Проверка: Успешное асинхронное создание инструмента со всеми валидными полями.
        """
        # Используем нативный асинхронный метод acreate() из Django 6.x
        instrument = await FinancialInstrument.objects.acreate(
            **valid_instrument_data
        )

        assert instrument.pk == valid_instrument_data["uid"]
        assert instrument.ticker == "SBER"
        assert instrument.min_price_increment == Decimal("0.010000000")
        assert instrument.klong == Decimal("0.15000000")
        assert instrument.api_trade_available_flag is True

    async def test_string_representation(self, valid_instrument_data):
        """
        Проверка: Метод __str__ возвращает строгий ожидаемый формат TICKER - NAME.
        """
        instrument = await FinancialInstrument.objects.acreate(
            **valid_instrument_data
        )
        assert str(instrument) == "SBER - Сбербанк России"

    async def test_unique_figi_constraint(self, valid_instrument_data):
        """
        Проверка: Поле figi имеет ограничение unique=True.
        Попытка создать дубликат figi должна вызывать IntegrityError.
        """
        # Создаем первый инструмент
        await FinancialInstrument.objects.acreate(**valid_instrument_data)

        # Модифицируем UID и тикер для второго, но оставляем тот же FIGI
        invalid_data = valid_instrument_data.copy()
        invalid_data["uid"] = uuid.uuid4()
        invalid_data["ticker"] = "SBER_P"

        # Проверяем, что СУБД блокирует транзакцию
        with pytest.raises(IntegrityError):
            await FinancialInstrument.objects.acreate(**invalid_data)

    async def test_nullable_risk_coefficients(self, valid_instrument_data):
        """
        Проверка: Поля klong и kshort могут оставаться пустыми (null=True),
        если инструмент не допущен к маржинальной торговле через API.
        """
        valid_instrument_data["klong"] = None
        valid_instrument_data["kshort"] = None

        instrument = await FinancialInstrument.objects.acreate(
            **valid_instrument_data
        )

        assert instrument.klong is None
        assert instrument.kshort is None
