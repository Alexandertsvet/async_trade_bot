from django.utils import timezone
from t_tech.invest import Candle, OrderBook, Trade, Quotation, MarketDataResponse
from t_tech.invest.utils import decimal_to_quotation, quotation_to_decimal
import datetime
from enum import Enum
import orjson

def q_to_f(q: Quotation) -> float:
    """Безопасная конвертация котировок во float."""
    if not q:
        return 0.0
    return q.units + q.nano / 1_000_000_000
from decimal import Decimal
from enum import Enum
import orjson

def _orjson_default_handler(obj):
    """Кастомный обработчик для типов, которые orjson не сериализует напрямую."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


class MarketDataFastSerializer_:
    """
    Центральный сериализатор для обработки рыночных данных перед отправкой.
    Оптимизирован для работы в связке с orjson.
    """
    
    @classmethod
    def serialize_to_json(cls, response: MarketDataResponse) -> bytes | None:
        """
        Основной метод для высоконагруженного стриминга.
        Превращает response напрямую в байтовую JSON-строку.
        """
        data_dict = cls.serialize(response)
        if data_dict is None:
            return None
        
        return orjson.dumps(
            data_dict,
            option=orjson.OPT_PASSTHROUGH_DECIMAL,
            default=_orjson_default_handler
        )

    @classmethod
    def serialize(cls, response: MarketDataResponse) -> dict | None:
        """Определяет тип пакета и вызывает нужный метод трансформации в dict."""
        if response.candle:
            return cls._serialize_candle(response.candle)
        if response.orderbook:
            return cls._serialize_orderbook(response.orderbook)
        if response.trade:
            return cls._serialize_trade(response.trade)
        return None

    @classmethod
    def _serialize_candle(cls, c) -> dict:
        return {
            "figi": c.figi,
            "ticker": getattr(c, 'ticker', None),
            "class_code": getattr(c, 'class_code', None),
            "instrument_uid": getattr(c, 'instrument_uid', None),
            "interval": c.interval,
            "open": quotation_to_decimal(c.open),
            "high": quotation_to_decimal(c.high),
            "low": quotation_to_decimal(c.low),
            "close": quotation_to_decimal(c.close),
            "volume": c.volume,
            "volume_buy": getattr(c, 'volume_buy', 0),
            "volume_sell": getattr(c, 'volume_sell', 0),
            "time": c.time,
            "last_trade_ts": getattr(c, 'last_trade_ts', None),
            "candle_source_type": getattr(c, 'candle_source_type', None),
        }

    @classmethod
    def _serialize_orderbook(cls, ob) -> dict:
        return {
            "figi": ob.figi,
            "ticker": getattr(ob, 'ticker', None),
            "class_code": getattr(ob, 'class_code', None),
            "instrument_uid": getattr(ob, 'instrument_uid', None), 
            "depth": ob.depth,
            "is_consistent": ob.is_consistent,
            "time": ob.time,
            "limit_up": quotation_to_decimal(ob.limit_up) if getattr(ob, 'limit_up', None) else None,
            "limit_down": quotation_to_decimal(ob.limit_down) if getattr(ob, 'limit_down', None) else None,
            "bids": [{"price": quotation_to_decimal(i.price), "quantity": i.quantity} for i in ob.bids],
            "asks": [{"price": quotation_to_decimal(i.price), "quantity": i.quantity} for i in ob.asks],
            "order_book_type": getattr(ob, 'order_book_type', None),
        }

    @classmethod
    def _serialize_trade(cls, t) -> dict:
        return {
            "figi": t.figi,
            "ticker": getattr(t, 'ticker', None),
            "class_code": getattr(t, 'class_code', None),
            "instrument_uid": getattr(t, 'instrument_uid', None),
            "trade_id": t.trade_id,
            "direction": t.direction,
            "price": quotation_to_decimal(t.price),
            "quantity": t.quantity,
            "time": t.time,
            "trade_source": getattr(t, 'trade_source', None),
        }

    @classmethod
    def serialize_candle(cls, c) -> dict:
        return {
            "figi": c.figi,
            "ticker": getattr(c, 'ticker', None),
            "class_code": getattr(c, 'class_code', None),
            "instrument_uid": getattr(c, 'instrument_uid', None),
            "interval": c.interval,
            "open": quotation_to_decimal(c.open),
            "high": quotation_to_decimal(c.high),
            "low": quotation_to_decimal(c.low),
            "close": quotation_to_decimal(c.close),
            "volume": c.volume,
            "volume_buy": getattr(c, 'volume_buy', 0),
            "volume_sell": getattr(c, 'volume_sell', 0),
            "time": c.time.isoformat() if isinstance(c.time, datetime.datetime) else str(c.time),
            "last_trade_ts": c.last_trade_ts.isoformat() if isinstance(c.last_trade_ts, datetime.datetime) else str(c.last_trade_ts),
            "candle_source_type": getattr(c, 'candle_source_type', None),
        }

    @classmethod
    def serialize_orderbook(cls, ob) -> dict:
        return {
            "figi": ob.figi,
            "ticker": getattr(ob, 'ticker', None),
            "class_code": getattr(ob, 'class_code', None),
            "instrument_uid": getattr(ob, 'instrument_uid', None), 
            "depth": ob.depth,
            "is_consistent": ob.is_consistent,
            "time": ob.time.isoformat() if isinstance(ob.time, datetime.datetime) else str(ob.time),
            "limit_up": quotation_to_decimal(ob.limit_up) if getattr(ob, 'limit_up', None) else None,
            "limit_down": quotation_to_decimal(ob.limit_down) if getattr(ob, 'limit_down', None) else None,
            "bids": [{"price": quotation_to_decimal(i.price), "quantity": i.quantity} for i in ob.bids],
            "asks": [{"price": quotation_to_decimal(i.price), "quantity": i.quantity} for i in ob.asks],
            "order_book_type": getattr(ob, 'order_book_type', None),
        }

    @classmethod
    def serialize_trade(cls, t) -> dict:
        return {
            "figi": t.figi,
            "ticker": getattr(t, 'ticker', None),
            "class_code": getattr(t, 'class_code', None),
            "instrument_uid": getattr(t, 'instrument_uid', None),
            "trade_id": t.trade_id,
            "direction": t.direction,
            "price": quotation_to_decimal(t.price),
            "quantity": t.quantity,
            "time": t.time.isoformat() if isinstance(t.time, datetime.datetime) else str(t.time),
            "trade_source": getattr(t, 'trade_source', None),
        }

import datetime
from enum import Enum
from decimal import Decimal
from typing import Dict, Any, Union

def to_float(val) -> float:
    """Универсальное приведение любых биржевых цен к float"""
    if not val:
        return 0.0
    # Если это Decimal или строка
    if isinstance(val, (Decimal, str, float, int)):
        return float(val)
    # Если это объект Quotation (units + nano)
    if hasattr(val, 'units') and hasattr(val, 'nano'):
        return float(val.units) + float(val.nano) / 1_000_000_000
    return float(val)

class MarketDataFastSerializer:
    @staticmethod
    def serialize_candle(c: Candle) -> Dict[str, Any]:
        """
        Сериализация свечи (Candle)

        Идентификаторы инструмента 
        figi (string, обязательное) — Уникальный глобальный идентификатор финансового инструмента (Financial Instrument Global Identifier).
        ticker (string | null) — Краткое биржевое наименование актива (например, SBER).
        class_code (string | null) — Идентификатор режима торгов на бирже (например, TQBR для акций на Мосбирже).
        instrument_uid (string | null) — Внутренний уникальный идентификатор инструмента в экосистеме Т-Инвестиций (GUID в формате строки).
        Параметры свечи 
        interval (integer) — Таймфрейм свечи в числовом эквиваленте (согласно SubscriptionInterval, где 1 соответствует минутному интервалу).
        open (float) — Цена открытия свечи в валюте инструмента.
        high (float) — Максимальная цена за период формирования свечи.
        low (float) — Минимальная цена за период формирования свечи.
        close (float) — Цена закрытия свечи за период (текущая цена для незавершенной свечи).
        Объемы торгов 
        volume (integer) — Общий объем торгов в этой свече, выраженный в лотах.
        volume_buy (integer) — Объем сделок на покупку (рыночные ордера по инициативе покупателя), в лотах. По умолчанию 0.
        volume_sell (integer) — Объем сделок на продажу (рыночные ордера по инициативе продавца), в лотах. По умолчанию 0.
        Временные метки
        time (string) — Время начала формирования свечи в формате ISO 8601 с указанием таймзоны (YYYY-MM-DDTHH:MM:SS+00:00).
        last_trade_ts (string) — Точное время последней зарегистрированной сделки, которая была включена в эту свечу. Формат ISO 8601.
        """
        return {
            "figi": c.figi,
            "ticker": getattr(c, 'ticker', None),
            "class_code": getattr(c, 'class_code', None),
            "instrument_uid": str(c.instrument_uid) if getattr(c, 'instrument_uid', None) else None,
            "interval": c.interval.value if isinstance(c.interval, Enum) else int(c.interval),
            "open": to_float(c.open),
            "high": to_float(c.high),
            "low": to_float(c.low),
            "close": to_float(c.close),
            "volume": int(c.volume),
            "volume_buy": int(getattr(c, 'volume_buy', 0)),
            "volume_sell": int(getattr(c, 'volume_sell', 0)),
            "time": c.time.isoformat() if isinstance(c.time, datetime.datetime) else str(c.time), 
            "last_trade_ts": c.last_trade_ts.isoformat() if isinstance(c.last_trade_ts, datetime.datetime) else str(c.last_trade_ts),
        }

    @staticmethod
    def serialize_orderbook(ob: OrderBook) -> Dict[str, Any]:
        """Сериализация биржевого стакана (OrderBook)"""
        bids = [{"p": to_float(getattr(b, 'price', b.get('price') if isinstance(b, dict) else b)), 
                 "q": int(getattr(b, 'quantity', b.get('quantity') if isinstance(b, dict) else b))} for b in ob.bids] if ob.bids else []
                 
        asks = [{"p": to_float(getattr(a, 'price', a.get('price') if isinstance(a, dict) else a)), 
                 "q": int(getattr(a, 'quantity', a.get('quantity') if isinstance(a, dict) else a))} for a in ob.asks] if ob.asks else []
        
        return {
            "figi": ob.figi,
            "instrument_uid": str(ob.instrument_uid) if getattr(ob, 'instrument_uid', None) else None,
            "depth": int(ob.depth),
            "is_consistent": bool(ob.is_consistent),
            "bids": bids,
            "asks": asks,
            "best_bid": bids[0]["p"] if bids else None, 
            "best_ask": asks[0]["p"] if asks else None, 
            "limit_up": to_float(ob.limit_up),
            "limit_down": to_float(ob.limit_down),
            "time": ob.time.isoformat() if isinstance(ob.time, datetime.datetime) else str(ob.time),
        }

    @staticmethod
    def serialize_trade(t: Trade) -> Dict[str, Any]:
        """Сериализация сделки из ленты (Trade)"""
        return {
            "figi": t.figi,
            "instrument_uid": str(t.instrument_uid) if getattr(t, 'instrument_uid', None) else None,
            "direction": t.direction.name if isinstance(t.direction, Enum) else str(t.direction),
            "price": to_float(t.price),
            "quantity": int(t.quantity),
            "time": t.time.isoformat() if isinstance(t.time, datetime.datetime) else str(t.time),
        }