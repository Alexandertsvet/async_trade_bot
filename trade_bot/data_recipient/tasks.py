import logging

import orjson
from celery import shared_task
from data_keeper.clickhouse_module import ClickHouseProcessor
from django.conf import settings
from redis import Redis

from data_recipient.functions import data_from_celery_to_clichouse

logger = logging.getLogger(__name__)

# Выносим константы, чтобы не хардкодить в теле функции
LOCK_KEY = "lock:flush_clickhouse"
QUEUE_KEY = "clickhouse_queue"
# На всякий случай увеличиваем до 2000, так как шаг стал реже (10с)
BATCH_SIZE = 2000


@shared_task(name="data_recipient.tasks.flush_redis_to_clickhouse")
def flush_redis_to_clickhouse():
    """
    celery -A trade_bot purge -f
    rm -f celerybeat-schedule
    celery -A trade_bot worker --loglevel=info --pool=solo -B
    """
    client_clickhouse = ClickHouseProcessor()
    redis_url = getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")
    redis_client = Redis.from_url(redis_url)

    # АТОМАРНАЯ БЛОКИРОВКА:
    # Защита на случай, если ClickHouse "задумается" дольше, чем на 10 секунд.
    # ex=8 секунд гарантирует, что старая блокировка гарантированно истечет
    # до прихода следующего планового тика от Beat (через 10с).
    lock_acquired = redis_client.set(LOCK_KEY, "true", ex=8, nx=True)
    if not lock_acquired:
        logger.info(
            "[CH_FLUSH] Прошлый таск еще не завершен. Пропуск дубликата."
        )
        return "DUPLICATE_IGNORED"

    try:
        # Атомарно выгребаем пачку и смотрим остаток
        pipe = redis_client.pipeline()
        pipe.lrange(QUEUE_KEY, 0, BATCH_SIZE - 1)
        pipe.ltrim(QUEUE_KEY, BATCH_SIZE, -1)
        pipe.llen(QUEUE_KEY)
        raw_data, _, queue_left = pipe.execute()

        # Если данных нет — просто выходим. Beat сам зайдет сюда через 10 секунд.
        if not raw_data:
            return "QUEUE_EMPTY"
        # Быстрая десериализация пачки
        batch = [orjson.loads(item) for item in raw_data]
        print(batch)

        data_from_celery_to_clichouse(batch, client_clickhouse)

        # Логируем работу воркера под фиксированным шагом Beat
        logger.info(
            f"[CH_FLUSH] [BEAT_MODE] // Обработано: {len(batch)} шт. "
            f"ОСТАТОК В ОЧЕРЕДИ: {queue_left}."
        )
        return f"PROCESSED_{len(batch)}_ITEMS"

    except Exception as e:
        logger.error(
            f"[CH_FLUSH] [CRITICAL_ERROR] Сбой при сбросе данных: {e}"
        )
        return "ERROR_OCCURRED"
