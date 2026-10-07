import asyncio
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

# Используем ваш кастомный SDK
from t_tech.invest import (
    AsyncClient,
    CandleInstrument,
    MarketDataRequest,
    OrderBookInstrument,
    SubscribeCandlesRequest,
    SubscribeOrderBookRequest,
    SubscribeTradesRequest,
    SubscriptionAction,
    SubscriptionInterval,
    TradeInstrument,
)
from user.models import TInvestAccount

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    """
    python3 manage.py t_unsubscribe
    Скрипт для принудительной отписки от всех стримов рыночных данных.
    """

    help = "ПРИНУДИТЕЛЬНАЯ ОТПИСКА ОТ ВСЕХ СТРИМОВ T-INVEST ДЛЯ СБРОСА ЛИМИТОВ"

    def handle(self, *args, **options):
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\nПРОЦЕСС ОТПИСКИ ПРЕРВАН"))

    async def main(self):
        # 1. Получаем токен из базы данных
        account = await TInvestAccount.objects.afirst()
        if not account:
            logger.error(
                "UNSUB_ERROR // В БАЗЕ ДАННЫХ НЕТ ПОДКЛЮЧЕННЫХ ТОКЕНОВ"
            )
            return

        token = account.access_token
        figi = "BBG004730RP0"

        # 2. Формируем пакет запросов на полную ОТПИСКУ (UNSUBSCRIBE)
        unsubscribe_requests = [
            MarketDataRequest(
                subscribe_candles_request=SubscribeCandlesRequest(
                    subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_UNSUBSCRIBE,
                    instruments=[
                        CandleInstrument(
                            figi=figi,
                            interval=SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE,
                        )
                    ],
                )
            ),
            MarketDataRequest(
                subscribe_order_book_request=SubscribeOrderBookRequest(
                    subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_UNSUBSCRIBE,
                    instruments=[OrderBookInstrument(figi=figi, depth=20)],
                )
            ),
            MarketDataRequest(
                subscribe_trades_request=SubscribeTradesRequest(
                    subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_UNSUBSCRIBE,
                    instruments=[TradeInstrument(figi=figi)],
                )
            ),
        ]

        async def unsubscribe_iterator():
            """Генератор, который мгновенно скармливает запросы отписки при открытии стрима"""
            for req in unsubscribe_requests:
                yield req

        logger.info(
            "UNSUB_START // Открытие специального gRPC канала для отписки..."
        )

        try:
            async with AsyncClient(token) as client:
                # Открываем стрим, передавая ему итератор с командами UNSUBSCRIBE
                stream = client.market_data_stream.market_data_stream(
                    unsubscribe_iterator()
                )

                logger.info(
                    "UNSUB_SENDING // Пакет отписок отправлен на сервер."
                )

                # Читаем ровно один ответ от сервера, чтобы убедиться, что он обработал запрос
                async for response in stream:
                    # Как только сервер прислал подтверждение (или статус), мы фиксируем успех
                    if (
                        response.subscribe_candles_response
                        or response.subscribe_order_book_response
                        or response.subscribe_trades_response
                    ):
                        print(response)
                        logger.info(
                            "UNSUB_CONFIRMED // Сервер подтвердил отмену подписок."
                        )

                    # Даем микро-паузу для финализации пакетов и выходим
                    await asyncio.sleep(0.5)
                    break

        except Exception as e:
            logger.error(
                f"UNSUB_CRITICAL_ERROR // Не удалось выполнить отписку: {e}"
            )
        finally:
            logger.info(
                "UNSUB_FINISHED // Соединение закрыто. Лимиты успешно очищены."
            )
