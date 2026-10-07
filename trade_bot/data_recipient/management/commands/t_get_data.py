import asyncio
import logging
import os
from decimal import Decimal

import orjson
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from redis.asyncio import Redis
from t_tech.invest import (
    AsyncClient,
    CandleInstrument,
    MarketDataRequest,
    MarketDataResponse,
    OrderBookInstrument,
    Quotation,
    SubscribeCandlesRequest,
    SubscribeOrderBookRequest,
    SubscribeTradesRequest,
    SubscriptionAction,
    SubscriptionInterval,
    TradeInstrument,
)
from user.models import TInvestAccount
from data_recipient.serializers import MarketDataFastSerializer

logger = logging.getLogger(__name__)
User = get_user_model()
TOKEN = os.getenv("INVEST_TOKEN")

FIGI = "BBG004730RP0"  # GAZP


def q_to_f(q: Quotation) -> float:
    if not q:
        return 0.0
    return q.units + q.nano / 1_000_000_000

class Command(BaseCommand):
    """
    python3 manage.py t_get_data
    """

    help = "ЗАПУСК АСИНХРОННОГО СТРИМА РЫНОЧНЫХ ДАННЫХ В WEBSOKETS T-INVEST"

    def handle(self, *args, **options):
        """Точка входа. Запускает асинхронный event loop."""
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nSTREAM_STREAM_STOPPED // СТРИМ ОСТАНОВЛЕН ПОЛЬЗОВАТЕЛЕМ"
                )
            )

    async def broadcast_to_terminal(
        self, group_name: str, event_type: str, payload: dict
    ):
        """Сверхбыстрая отправка в Redis с помощью orjson с поддержкой Decimal"""
        channel_layer = get_channel_layer()

        message_dict = {
            "event": event_type,
            "timestamp": timezone.now().strftime("%H:%M:%S"),
            **payload,
        }

        def default_encoder(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError

        json_bytes = orjson.dumps(
            message_dict,
            default=default_encoder,
            option=orjson.OPT_SERIALIZE_NUMPY,
        )

        json_str = json_bytes.decode("utf-8")

        await channel_layer.group_send(
            group_name, {"type": "stream_market_data", "content": json_str}
        )
        await self.redis_client.lpush("clickhouse_queue", json_str)

    async def handle_market_data(
        self,
        response: MarketDataResponse,
        group_name: str,
        curent_time_receive,
    ):
        """Обработка и немедленная трансляция данных в вебсокете"""
        curent_time_bs = curent_time_receive
        curent_time_bs_serialize = curent_time_bs.isoformat()
        if response.candle:
            payload = MarketDataFastSerializer.serialize_candle(
                response.candle
            )
            payload["time_resive_data"] = curent_time_bs_serialize
            last_trade_ts = response.candle.last_trade_ts
            NET_CANDLE_LAG = curent_time_bs - last_trade_ts
            curent_time_as = timezone.now()
            LAG_CANDLE_SERIALAZER = curent_time_as - curent_time_bs
            logger.info(
                f"STREAM//CANDL//NET_CANDLE_LAG: {NET_CANDLE_LAG}//LAG_CANDLE_SERIALAZER: {LAG_CANDLE_SERIALAZER}"
            )
            await self.broadcast_to_terminal(group_name, "CANDLE", payload)

        # 2. ОБРАБОТКА СТАКАНА
        elif response.orderbook:
            payload = MarketDataFastSerializer.serialize_orderbook(
                response.orderbook
            )
            payload["time_resive_data"] = curent_time_bs_serialize
            NET_ORDER_BOK_LAG = curent_time_bs - response.orderbook.time

            logger.info(
                f"STREAM//ORDERBOOK//NET_ORDER_BOK_LAG: {NET_ORDER_BOK_LAG}"
            )
            await self.broadcast_to_terminal(group_name, "ORDERBOOK", payload)

        # 3. ОБРАБОТКА ЛЕНТЫ СДЕЛОК
        elif response.trade:
            payload = MarketDataFastSerializer.serialize_trade(response.trade)
            payload["time_resive_data"] = curent_time_bs_serialize
            NET_TRADE_LAG = curent_time_bs - response.trade.time

            logger.info(f"STREAM//TRADE//NET_TRADE_LAG {NET_TRADE_LAG}")
            await self.broadcast_to_terminal(group_name, "TRADE", payload)

    async def main(self):

        redis_url = getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")
        print(f"// ИНИЦИАЛИЗАЦИЯ КЛИЕНТА: {redis_url}")

        # Явно создаем изолированный асинхронный клиент БЕЗ посредников
        client = Redis.from_url(redis_url, decode_responses=False)
        self.redis_client = client  # Присваиваем экземпляру класса

        try:
            # Метод ping() в redis.asyncio возвращает True/False, но сам по себе является корутиной
            is_alive = await self.redis_client.ping()
            if is_alive:
                logger.info(
                    "REDIS_CONNECTED // Асинхронный клиент Redis успешно запущен."
                )
            else:
                logger.error(
                    "REDIS_ERROR // Redis вернул некорректный ответ на PING."
                )
                return
        except Exception as e:
            logger.error(
                f"REDIS_ERROR // Не удалось подключиться к Redis: {e}"
            )
            return

        account = await TInvestAccount.objects.afirst()
        if not account:
            logger.error(
                "STREAM_ERROR // В БАЗЕ ДАННЫХ НЕТ ПОДКЛЮЧЕННЫХ ТОКЕНОВ"
            )
            return

        token = account.access_token
        figi = "BBG004730RP0"

        # Общая группа рассылки для всех открытых терминалов (можно сделать персональной для юзера)
        group_name = "market_data_broadcast"

        request_queue = asyncio.Queue()

        # Наполнение очереди запросов подписок
        await request_queue.put(
            MarketDataRequest(
                subscribe_candles_request=SubscribeCandlesRequest(
                    subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                    instruments=[
                        CandleInstrument(
                            figi=figi,
                            interval=SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE,
                        )
                    ],
                )
            )
        )
        await request_queue.put(
            MarketDataRequest(
                subscribe_order_book_request=SubscribeOrderBookRequest(
                    subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                    instruments=[OrderBookInstrument(figi=figi, depth=20)],
                )
            )
        )
        await request_queue.put(
            MarketDataRequest(
                subscribe_trades_request=SubscribeTradesRequest(
                    subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                    instruments=[TradeInstrument(figi=figi)],
                )
            )
        )

        async def request_iterator():
            while True:
                request = await request_queue.get()
                yield request
                request_queue.task_done()

        logger.info("STREAM_CONNECTING // УСТАНОВКА СОЕДИНЕНИЯ С T-INVEST...")

        try:
            async with AsyncClient(token) as client:
                async for (
                    marketdata
                ) in client.market_data_stream.market_data_stream(
                    request_iterator()
                ):
                    curent_time_receive = timezone.now()
                    await self.handle_market_data(
                        marketdata, group_name, curent_time_receive
                    )

        except asyncio.CancelledError:
            logger.warning("STREAM_CANCELLED // РАБОТА СТРИМА АННУЛИРОВАНА")
            await request_queue.put(
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
                )
            )
            await request_queue.put(
                MarketDataRequest(
                    subscribe_order_book_request=SubscribeOrderBookRequest(
                        subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_UNSUBSCRIBE,
                        instruments=[OrderBookInstrument(figi=figi, depth=20)],
                    )
                )
            )
            await request_queue.put(
                MarketDataRequest(
                    subscribe_trades_request=SubscribeTradesRequest(
                        subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_UNSUBSCRIBE,
                        instruments=[TradeInstrument(figi=figi)],
                    )
                )
            )

            logger.info(
                "STREAM_CLOSED // Все gRPC соединения успешно закрыты."
            )
        except Exception as e:
            logger.error(f"STREAM_CRITICAL_ERROR // ОШИБКА: {e}")
        finally:
            if self.redis_client:
                await self.redis_client.aclose()
                logger.info(
                    "REDIS_CLOSED // Пул соединений Redis успешно очищен."
                )
