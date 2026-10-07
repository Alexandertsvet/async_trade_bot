import datetime
import logging
from uuid import UUID

import orjson
from django.utils import timezone

logger = logging.getLogger(__name__)


def data_from_celery_to_clichouse(raw_data, client):
    if not raw_data:
        logger.debug(
            "[CH_ADAPTIVE] // Очередь пуста. Ждем следующий тик планировщика."
        )
        return "QUEUE_EMPTY"

    # Раздельные батчи под каждую целевую таблицу
    candles_batch = []
    orderbooks_batch = []
    trades_batch = []
    corrupted_items = 0

    # Текущее время для логирования/фоллбэка, если в JSON нет time_resive_data
    now_str = timezone.now().isoformat()

    for item in raw_data:
        try:
            if isinstance(item, (dict, list)):
                data = item
                event_type = data.get("event")
            else:
                data = orjson.loads(item)
                event_type = data.get("event")

            # Общие поля, которые часто приходят в рыночных данных (добавлен фоллбэк)
            instrument_uid = data.get("instrument_uid")
            # clickhouse-driver принимает UUID как строку или объект UUID.
            # Если в JSON валидная строка UUID, можно оставить строкой, либо валидировать:
            if instrument_uid:
                try:
                    instrument_uid = str(UUID(instrument_uid))
                except ValueError:
                    instrument_uid = "00000000-0000-0000-0000-000000000000"
            else:
                instrument_uid = "00000000-0000-0000-0000-000000000000"

            if event_type == "CANDLE":
                candles_batch.append(
                    {
                        "figi": data.get("figi", ""),
                        "ticker": data.get("ticker", ""),
                        "class_code": data.get("class_code", ""),
                        "instrument_uid": instrument_uid,
                        "interval": int(data.get("interval", 0)),
                        "open": float(data.get("open", 0.0)),
                        "high": float(data.get("high", 0.0)),
                        "low": float(data.get("low", 0.0)),
                        "close": float(data.get("close", 0.0)),
                        "volume": int(data.get("volume", 0)),
                        "volume_buy": int(data.get("volume_buy", 0)),
                        "volume_sell": int(data.get("volume_sell", 0)),
                        "time": datetime.datetime.fromisoformat(
                            data.get("time", now_str)
                        ),
                        "last_trade_ts": datetime.datetime.fromisoformat(
                            data.get("last_trade_ts", now_str)
                        ),
                        "time_resive_data": datetime.datetime.fromisoformat(
                            data.get("time_resive_data", now_str)
                        ),
                    }
                )

            elif event_type == "ORDERBOOK":
                bids_list = data.get("bids", [])
                asks_list = data.get("asks", [])

                orderbooks_batch.append(
                    {
                        "figi": data.get("figi", ""),
                        "instrument_uid": instrument_uid,
                        "depth": int(data.get("depth", 0)),
                        "is_consistent": bool(data.get("is_consistent", True)),
                        "bids.p": [
                            float(b["p"]) for b in bids_list if "p" in b
                        ],
                        "bids.q": [int(b["q"]) for b in bids_list if "q" in b],
                        "asks.p": [
                            float(a["p"]) for a in asks_list if "p" in a
                        ],
                        "asks.q": [int(a["q"]) for a in asks_list if "q" in a],
                        "best_bid": float(data.get("best_bid", 0.0)),
                        "best_ask": float(data.get("best_ask", 0.0)),
                        "limit_up": float(data.get("limit_up", 0.0)),
                        "limit_down": float(data.get("limit_down", 0.0)),
                        "time": datetime.datetime.fromisoformat(
                            data.get("time", now_str)
                        ),
                        "time_resive_data": datetime.datetime.fromisoformat(
                            data.get("time_resive_data", now_str)
                        ),
                    }
                )

            elif event_type == "TRADE":
                # Защита для Enum8. Значение должно строго совпадать с одной из строк в схеме.
                direction = data.get(
                    "direction", "TRADE_DIRECTION_UNSPECIFIED"
                )
                if direction not in (
                    "TRADE_DIRECTION_UNSPECIFIED",
                    "TRADE_DIRECTION_BUY",
                    "TRADE_DIRECTION_SELL",
                ):
                    direction = "TRADE_DIRECTION_UNSPECIFIED"

                trades_batch.append(
                    {
                        "figi": data.get("figi", ""),
                        "instrument_uid": instrument_uid,
                        "direction": direction,
                        "price": float(data.get("price", 0.0)),
                        "quantity": int(data.get("quantity", 0)),
                        "time": datetime.datetime.fromisoformat(
                            data.get("time", now_str)
                        ),
                        "time_resive_data": datetime.datetime.fromisoformat(
                            data.get("time_resive_data", now_str)
                        ),
                    }
                )

        except Exception as e:
            logger.error(f"CH_PARSE_ERROR // Ошибка подготовки записи: {e}")
            corrupted_items += 1
            continue

    try:
        if candles_batch:
            client.execute(
                """INSERT INTO trade_db.candles 
                       (figi, ticker, class_code, instrument_uid, interval, open, high, low, close, volume, volume_buy, volume_sell, time, last_trade_ts, time_resive_data) 
                       VALUES""",
                candles_batch,
            )
        if orderbooks_batch:
            client.execute(
                """INSERT INTO trade_db.orderbooks 
                       (figi, instrument_uid, depth, is_consistent, `bids.p`, `bids.q`, `asks.p`, `asks.q`, best_bid, best_ask, limit_up, limit_down, time, time_resive_data) 
                       VALUES""",
                orderbooks_batch,
            )
        if trades_batch:
            client.execute(
                """INSERT INTO trade_db.trades 
                       (figi, instrument_uid, direction, price, quantity, time, time_resive_data) 
                       VALUES""",
                trades_batch,
            )

        total_inserted = (
            len(candles_batch) + len(orderbooks_batch) + len(trades_batch)
        )
        logger.info(
            f"[CH_FLUSH] // Успешно записано: {total_inserted} строк. Сбойных JSON: {corrupted_items}."
        )

    except Exception as ch_err:
        logger.error(
            f"CH_WRITE_CRITICAL // Сбой ClickHouse! Возврат пачки в Redis. Ошибка: {ch_err}"
        )
