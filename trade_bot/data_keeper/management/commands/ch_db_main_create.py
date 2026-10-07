import logging

from data_keeper.clickhouse_module import ClickHouseProcessor
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    python3 manage.py ch_db_main_create
    """

    help = "Инициализация базы данных clichouse."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("//ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ"))
        client_clickhouse = ClickHouseProcessor()
        self.stdout.write(
            self.style.SUCCESS(
                f"[ClickHouseProcessor]//{client_clickhouse}//УСПЕШНО ИМПОРТИРОВАН."
            )
        )
        self.stdout.write(
            self.style.MIGRATE_LABEL(
                "[ClickHouseProcessor]//СОЗДАНИЕ ОСНОВНОЙ БАЗЫ ДАННЫХ."
            )
        )
        client_clickhouse.create_main_db(db_name="trade_db")
        self.stdout.write(
            self.style.SUCCESS(
                "[ClickHouseProcessor]//БАЗА ДАННЫХ УСПЕШНО СОЗДАНА ИЛИ УЖЕ СУЩЕСТВУЕТ."
            )
        )
        self.stdout.write(
            self.style.MIGRATE_LABEL("[ClickHouseProcessor]//СОЗДАНИЕ ТАБЛИЦ.")
        )
        client_clickhouse.create_main_table()
        self.stdout.write(
            self.style.SUCCESS(
                "[ClickHouseProcessor]//ТАБЛИЦА УСПЕШНО СОЗДАНА ИЛИ УЖЕ СУЩЕСТВУЕТ."
            )
        )

        # client_clickhouse.drop("trade_db.candles")
        # client_clickhouse.drop("trade_db.orderbooks")
        # client_clickhouse.drop("trade_db.trades")
