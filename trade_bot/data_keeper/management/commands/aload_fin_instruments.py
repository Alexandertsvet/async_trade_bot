import asyncio

from data_keeper.models import FinancialInstrument
from django.core.management.base import BaseCommand
from django.utils import timezone
from t_tech.invest import AsyncClient, SecurityTradingStatus
from t_tech.invest.utils import quotation_to_decimal
from trade_bot.settings import INVEST_TOKEN


class Command(BaseCommand):
    """
    python3 manage.py aload_fin_instruments
    """

    help = "Модель финансового инструмента на основе данных T-Invest API."

    async def fetch_category_instruments(
        self, client, method_name, current_time
    ):
        """Асинхронно запрашивает инструменты одной категории и парсит их."""
        self.stdout.write(f"Запрос инструментов категории: {method_name}")

        instruments_service = client.instruments
        api_method = getattr(instruments_service, method_name)

        # Выполняем асинхронный сетевой запрос
        api_response = await api_method()

        parsed_instruments = []
        for item in api_response.instruments:
            nano_val = getattr(item.min_price_increment, "nano", 0)
            scale = 9 - len(str(nano_val)) + 1

            instrument_obj = FinancialInstrument(
                uid=item.uid,
                figi=item.figi,
                ticker=item.ticker,
                class_code=item.class_code,
                name=item.name,
                type=method_name,
                exchange=item.exchange,
                currency=item.currency,
                lot=item.lot,
                min_price_increment=quotation_to_decimal(
                    item.min_price_increment
                ),
                scale=scale,
                trading_status=str(
                    SecurityTradingStatus(item.trading_status).name
                ),
                api_trade_available_flag=item.api_trade_available_flag,
                buy_available_flag=item.buy_available_flag,
                sell_available_flag=item.sell_available_flag,
                short_enabled_flag=item.short_enabled_flag,
                klong=quotation_to_decimal(item.klong),
                kshort=quotation_to_decimal(item.kshort),
                updated_at=current_time,
            )
            parsed_instruments.append(instrument_obj)

        return parsed_instruments

    async def _async_handle(self):
        """Внутренний асинхронный метод для выполнения всей логики."""
        fin_instrument = await FinancialInstrument.objects.all().acount()
        self.stdout.write(
            self.style.SUCCESS(f"Кол-во объектов в базе: {fin_instrument}")
        )
        self.stdout.write("Начало загрузки данных из API...")

        methods = ["shares", "bonds", "etfs", "currencies", "futures"]
        current_time = timezone.now()
        async with AsyncClient(INVEST_TOKEN) as client:
            tasks = [
                self.fetch_category_instruments(client, method, current_time)
                for method in methods
            ]
            results = await asyncio.gather(*tasks)

        # Объединяем списки результатов
        instruments_data = [item for sublist in results for item in sublist]

        if not instruments_data:
            self.stdout.write(
                self.style.WARNING("Данные для импорта отсутствуют.")
            )
            return

        self.stdout.write(
            f"Получено {len(instruments_data)} инструментов. Запись в PostgreSQL..."
        )

        fields_to_update = [
            "figi",
            "ticker",
            "class_code",
            "name",
            "type",
            "exchange",
            "currency",
            "lot",
            "min_price_increment",
            "scale",
            "trading_status",
            "api_trade_available_flag",
            "buy_available_flag",
            "sell_available_flag",
            "short_enabled_flag",
            "klong",
            "kshort",
            "updated_at",
        ]

        await FinancialInstrument.objects.abulk_create(
            instruments_data,
            batch_size=1000,
            update_conflicts=True,
            unique_fields=["uid"],
            update_fields=fields_to_update,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно импортировано/обновлено инструментов: {len(instruments_data)}"
            )
        )

        fin_instrument_final = await FinancialInstrument.objects.all().acount()
        self.stdout.write(
            self.style.SUCCESS(
                f"Кол-во объектов в базе после обновления: {fin_instrument_final}"
            )
        )

    def handle(self, *args, **kwargs):
        """Точка входа Django. Запускает асинлайн-цикл событий."""
        asyncio.run(self._async_handle())
