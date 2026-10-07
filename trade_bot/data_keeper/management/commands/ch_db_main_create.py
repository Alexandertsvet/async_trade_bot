from django.core.management.base import BaseCommand
import logging
from django.conf import settings
from data_keeper.clickhouse_module import ClickHouseProcessor
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    python3 manage.py ch_db_main_create
    """

    help = "Инициализация базы данных clichouse."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS(f"//ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ"))
        client_clickhouse = ClickHouseProcessor()
        self.stdout.write(self.style.SUCCESS(f"[ClickHouseProcessor]//{client_clickhouse}//УСПЕШНО ИМПОРТИРОВАН."))
        self.stdout.write(self.style.MIGRATE_LABEL(f"[ClickHouseProcessor]//СОЗДАНИЕ ОСНОВНОЙ БАЗЫ ДАННЫХ."))
        client_clickhouse.create_main_db(db_name="trade_db")
        self.stdout.write(self.style.SUCCESS(f"[ClickHouseProcessor]//БАЗА ДАННЫХ УСПЕШНО СОЗДАНА ИЛИ УЖЕ СУЩЕСТВУЕТ."))
        self.stdout.write(self.style.MIGRATE_LABEL(f"[ClickHouseProcessor]//СОЗДАНИЕ ТАБЛИЦ."))
        client_clickhouse.create_main_table()
        self.stdout.write(self.style.SUCCESS(f"[ClickHouseProcessor]//ТАБЛИЦА УСПЕШНО СОЗДАНА ИЛИ УЖЕ СУЩЕСТВУЕТ."))

        #client_clickhouse.drop("trade_db.candles")
        #client_clickhouse.drop("trade_db.orderbooks")
        #client_clickhouse.drop("trade_db.trades")