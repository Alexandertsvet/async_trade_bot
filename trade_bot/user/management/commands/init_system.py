import asyncio
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from t_tech.invest import AsyncClient
from t_tech.invest.exceptions import AioUnauthenticatedError, RequestError

from user.models import TInvestAccount

User = get_user_model()
load_dotenv()


class Command(BaseCommand):
    help = "инициализация системы через .env file"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Начало инициализации системы!"))
        ENV_FILE = (
            settings.BASE_DIR.parent / ".env" or settings.BASE_DIR / ".env"
        )
        if not ENV_FILE.is_file():
            self.stdout.write(
                self.style.ERROR("В системе не обнаружен .env файл!")
            )
            self.stdout.write(
                self.style.ERROR("Инициализация системы завершена с ошибкой!")
            )
            raise ImproperlyConfigured(
                f"Критическая ошибка: Файл конфигурации {ENV_FILE} отсутствует! "
                f"Создайте его на основе .env.example перед запуском проекта."
            )
        self.stdout.write(
            self.style.MIGRATE_LABEL("В системе обнаружен .env файл!")
        )
        SECRET_KEY = os.getenv("SECRET_KEY")
        DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
        INVEST_TOKEN = os.getenv("INVEST_TOKEN")
        FIELD_ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY")
        REQUIRED_ENV_FIELDS = {
            "SECRET_KEY": SECRET_KEY,
            "INVEST_TOKEN": INVEST_TOKEN,
            "FIELD_ENCRYPTION_KEY": FIELD_ENCRYPTION_KEY,
        }
        missing_fields = [
            key for key, value in REQUIRED_ENV_FIELDS.items() if not value
        ]

        if missing_fields:
            self.stdout.write(
                self.style.ERROR(
                    f"Проверте .env файл? отсутствует {missing_fields}"
                )
            )
            raise ImproperlyConfigured(
                f"В файле .env отсутствуют или не заполнены обязательные переменные: "
                f"{', '.join(missing_fields)}"
            )
        self.stdout.write(self.style.SUCCESS(".ENV ФАЙЛ СТАТУС ПРОВЕРЕН!"))

        self.stdout.write(
            self.style.MIGRATE_LABEL("ПРОВЕРКА API KEY INVEST_TOKEN!")
        )

        async def check_api():
            async with AsyncClient(INVEST_TOKEN) as client:
                try:
                    accounts = await client.users.get_accounts()
                    return accounts
                except RequestError as e:
                    if e.code.name == "UNAUTHENTICATED":
                        raise AioUnauthenticatedError(
                            code=e.code, details=e.details, metadata=e.metadata
                        ) from e
                    raise e

        accounts = asyncio.run(check_api())
        if not accounts:
            self.stdout.write(
                self.style.ERROR(f"Аккаунт не найден {accounts}")
            )

        self.stdout.write(
            self.style.MIGRATE_LABEL(f"Аккаунт не найден {accounts}")
        )

        async def get_or_create_account(accounts):
            self.stdout.write(
                self.style.MIGRATE_LABEL("СОХРАНЕНИЕ ДАННЫХ В БАЗУ!")
            )
            created_accounts = []
            user = await User.objects.afirst()
            if user:
                for account in accounts.accounts:
                    (
                        account_db,
                        created,
                    ) = await TInvestAccount.objects.aget_or_create(
                        user=user,
                        account_id=account.id,
                        access_token=INVEST_TOKEN,
                        description=account.name,
                        type=account.type,
                        status=account.status,
                        access_level=account.access_level,
                        opened_date=account.opened_date,
                        closed_date=account.closed_date,
                    )
                    if created:
                        self.stdout.write(
                            self.style.MIGRATE_LABEL(
                                f"Аккаунт {account_db.user} успешно добавлен!"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.MIGRATE_LABEL(
                                f"Аккаунт {account_db.user} уже существовал в базе данных."
                            )
                        )
                    return created_accounts.append(account_db)
                return created_accounts
            else:
                self.stdout.write(
                    self.style.MIGRATE_LABEL(
                        f"Для успешнйо инициализации системы необходим user, из базы извлечено значение: {user}!"
                    )
                )

        accounts_db_list = asyncio.run(get_or_create_account(accounts))
        print(accounts_db_list)

        status_account = accounts.accounts[0].status
        account_access = accounts.accounts[0].access_level
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Статус аккаунта {status_account.name}"
            )
        )
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"Доступ {account_access.name}")
        )
        if status_account == 2 and account_access == 1:
            self.stdout.write(
                self.style.SUCCESS(
                    "Для аккаунта возможна торговля в реальном времени через систему!"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Для аккаунта не возможна торговля или ограничена!"
                    "Статус аккаунта должен ACCOUNT_STATUS_OPEN"
                    "Доступ ACCOUNT_ACCESS_LEVEL_FULL_ACCESS"
                )
            )
        self.stdout.write(
            self.style.SUCCESS("API KEY INVEST_TOKEN СТАТУС ПРОВЕРЕН!")
        )

        self.stdout.write(
            self.style.SUCCESS("Инициализация системы выполнена!")
        )
