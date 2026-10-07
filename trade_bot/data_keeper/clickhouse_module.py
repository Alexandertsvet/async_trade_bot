import logging
import os

from clickhouse_driver import Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()
print("//CLICHOUSE DRIVER")
IS_DOCKER = os.getenv("DOCKER_ENV", "False").lower() in ("true", "1", "t")
print(f"//Запущено в Docker: {IS_DOCKER}")
if IS_DOCKER:
    CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST")
    CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_PORT")
    CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER")
    CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD")
else:
    CLICKHOUSE_HOST = "localhost"
    CLICKHOUSE_PORT = 9000
    CLICKHOUSE_USER = "default"
    CLICKHOUSE_PASSWORD = "default"


class ClickHouseProcessor(Client):
    def __init__(self, host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT):
        super().__init__(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            user=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
        )

    def drop(self, table_name):
        """Удаленеи таблицы table"""
        query = f"""
        DROP TABLE IF EXISTS {table_name}
        """
        try:
            self.execute(query)
            logger.info(f"Таблица {table_name} успешно удалена.")
        except Exception as e:
            logger.exception(f"Ошибка при удалении таблицы {table_name}: {e}")
            raise e

    def truncate_table(self, db, table_name):
        "Очистка данных в таблице"
        query = f"""
        TRUNCATE TABLE IF EXISTS {db}.{table_name}
        """
        try:
            self.execute(query)
            logging.error(e)(
                f"выполнена очистка данных таблицы {db}.{table_name}"
            )
        except Exception as e:
            logging.error(e)(
                f"error: {e}, при очистки таблицы {db}.{table_name}"
            )

    def get_report(self, limit=100, table="test_tradestats"):
        """
        Возвращает отчет о последних выполненных запросах из системного лога.
        Требует прав доступа к таблице system.query_log.
        """
        report_sql = f"""
        SELECT 
            event_time,
            query, 
            query_duration_ms / 1000 AS seconds, 
            read_rows, 
            formatReadableSize(read_bytes) AS memory
        FROM system.query_log
        WHERE query LIKE '%{table}%' AND type = 'QueryFinish' AND query NOT LIKE '%system.query_log%' 
        ORDER BY event_time DESC
        LIMIT {limit}
        """
        return self.query_dataframe(report_sql)

    def drop_duplicated(self, db, table="test_tradestats"):
        """
        Удаление дубликатов в таблице
        """
        return self.execute(f"OPTIMIZE TABLE {db}.{table} FINAL")

    def create_main_db(self, db_name="trade_db"):
        """
        Создание главной базы данных.
        db_name='trade_db'
        """
        try:
            create_db_query = f"CREATE DATABASE IF NOT EXISTS {db_name}"
            self.execute(create_db_query)
            self.execute(f"USE {db_name}")
            logger.info(
                f"[ClickHouseProcessor]//База данных '{db_name}' успешно создана или уже существует."
            )
        except Exception as e:
            logger.error(
                f"[ClickHouseProcessor]//База данных '{db_name}' Ошибка при создании БД/таблицы: {e}."
            )

    def create_main_table(self):
        """
        Создание главной таблицы.

        """

        schemes = [
            """
        CREATE TABLE IF NOT EXISTS trade_db.candles
        (
            `figi` String,
            `ticker` LowCardinality(String),
            `class_code` LowCardinality(String),
            `instrument_uid` UUID,
            `interval` UInt8,
            `open` Decimal(18, 4),
            `high` Decimal(18, 4),
            `low` Decimal(18, 4),
            `close` Decimal(18, 4),
            `volume` UInt64,
            `volume_buy` UInt64,
            `volume_sell` UInt64,
            `time` DateTime64(0, 'UTC'),
            `last_trade_ts` DateTime64(6, 'UTC'),
            `time_resive_data` DateTime64(6, 'UTC')
        )
        ENGINE = MergeTree()
        PARTITION BY toYYYYMMDD(time)
        ORDER BY (instrument_uid, interval, time);
        """,
            """
        CREATE TABLE IF NOT EXISTS trade_db.orderbooks
        (
            `figi` String,
            `instrument_uid` UUID,
            `depth` UInt8,
            `is_consistent` Bool,
            
            -- Стакан на покупку (Bids)
            `bids.p` Array(Decimal(18, 4)),
            `bids.q` Array(UInt64),
            
            -- Стакан на продажу (Asks)
            `asks.p` Array(Decimal(18, 4)),
            `asks.q` Array(UInt64),
            
            `best_bid` Decimal(18, 4),
            `best_ask` Decimal(18, 4),
            `limit_up` Decimal(18, 4),
            `limit_down` Decimal(18, 4),
            `time` DateTime64(6, 'UTC'),
            `time_resive_data` DateTime64(6, 'UTC')
        )
        ENGINE = MergeTree()
        PARTITION BY toYYYYMMDD(time) 
        ORDER BY (instrument_uid, time);
        """,
            """
        CREATE TABLE IF NOT EXISTS trade_db.trades
        (
            `figi` String,
            `instrument_uid` UUID,
            `direction` Enum8('TRADE_DIRECTION_UNSPECIFIED' = 0, 'TRADE_DIRECTION_BUY' = 1, 'TRADE_DIRECTION_SELL' = 2),
            `price` Decimal(18, 4),
            `quantity` UInt64,
            `time` DateTime64(6, 'UTC'),
            `time_resive_data` DateTime64(6, 'UTC')
        )
        ENGINE = MergeTree()
        PARTITION BY toYYYYMMDD(time)
        ORDER BY (instrument_uid, time);
        """,
        ]
        for scheme in schemes:
            try:
                self.execute(scheme)
                logger.info(
                    "[ClickHouseProcessor]//База данных успешно создана или уже существует."
                )
            except Exception as e:
                logger.error(
                    f"[ClickHouseProcessor]//База данных Ошибка при создании БД/таблицы: {e}."
                )


# создание базы данных
def create_db(client, db_name, table_name):
    try:
        create_db_query = f"CREATE DATABASE IF NOT EXISTS {db_name}"
        client.execute(create_db_query)

        client.execute(f"USE {db_name}")
        print(f"База данных '{db_name}' успешно создана или уже существует")

        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {db_name}.{table_name} (
              
            )
            ENGINE = ReplacingMergeTree()
            ORDER BY (secid, tradedate, tradetime)
            """

        client.execute(create_table_query)
        print(f"Таблица '{table_name}' успешно создана в БД '{db_name}'")

        result = client.execute(f"DESCRIBE TABLE {table_name}")

        for row in result:
            print(f"  {row[0]}: {row[1]}")

    except Exception as e:
        print(f"Ошибка при создании БД/таблицы: {e}")
        return False
    finally:
        if "client" in locals():
            client.disconnect()


"""
CREATE TABLE trade_db.candles
(
    `figi` String,
    `ticker` LowCardinality(String),
    `class_code` LowCardinality(String),
    `instrument_uid` UUID,
    `interval` UInt8,
    `open` Decimal(18, 4),
    `high` Decimal(18, 4),
    `low` Decimal(18, 4),
    `close` Decimal(18, 4),
    `volume` UInt64,
    `volume_buy` UInt64,
    `volume_sell` UInt64,
    `time` DateTime64(0, 'UTC'),
    `last_trade_ts` DateTime64(6, 'UTC'),
    `time_resive_data` DateTime64(6, 'UTC')
)
ENGINE = ReplacingMergeTree(time_resive_data)
PARTITION BY toYYYYMM(time)
ORDER BY (ticker, class_code, time);
"""

"""
CREATE TABLE trade_db.orderbooks
(
    `figi` String,
    `instrument_uid` UUID,
    `depth` UInt8,
    `is_consistent` Bool,
    
    -- Стакан на покупку (Bids)
    `bids.p` Array(Decimal(18, 4)),
    `bids.q` Array(UInt64),
    
    -- Стакан на продажу (Asks)
    `asks.p` Array(Decimal(18, 4)),
    `asks.q` Array(UInt64),
    
    `best_bid` Decimal(18, 4),
    `best_ask` Decimal(18, 4),
    `limit_up` Decimal(18, 4),
    `limit_down` Decimal(18, 4),
    `time` DateTime64(6, 'UTC'),
    `time_resive_data` DateTime64(6, 'UTC')
)
ENGINE = ReplacingMergeTree(time_resive_data)
PARTITION BY toYYYYMMDD(time)
ORDER BY (instrument_uid, time);
"""

"""
CREATE TABLE trade_db.trades
(
    `figi` String,
    `instrument_uid` UUID,
    `direction` Enum8('TRADE_DIRECTION_UNSPECIFIED' = 0, 'TRADE_DIRECTION_BUY' = 1, 'TRADE_DIRECTION_SELL' = 2),
    `price` Decimal(18, 4),
    `quantity` UInt64,
    `time` DateTime64(6, 'UTC'),
    `time_resive_data` DateTime64(6, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(time)
ORDER BY (instrument_uid, time);
"""
