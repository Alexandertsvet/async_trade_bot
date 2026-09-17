import logging

from django.core.exceptions import ValidationError
from django.utils import timezone
from t_tech.invest import AsyncClient
from t_tech.invest.exceptions import RequestError

from user.models import TInvestAccount

logger = logging.getLogger(__name__)


async def check_and_sync_tinvest_accounts(user, invest_token: str):
    """
    Проверяет валидность токена через API Т-Инвестиций.
    Если токен валиден, находит все связанные аккаунты и асинхронно
    сохраняет новые в базу данных для текущего пользователя.
    """
    async with AsyncClient(invest_token) as client:
        try:
            api_response = await client.users.get_accounts()
            accounts_list = api_response.accounts
        except RequestError as e:
            tracking_id = e.metadata.tracking_id if e.metadata else ""
            logger.error(
                f"Ошибка API Т-Инвестиций: tracking_id={tracking_id} code={str(e.code)}"
            )

            if e.code.name == "UNAUTHENTICATED":
                raise ValidationError(
                    "УКАЗАННЫЙ ТОКЕН НЕВАЛИДЕН ИЛИ ЕГО СРОК ДЕЙСТВИЯ ИСТЕК."
                )

            raise ValidationError(f"ОШИБКА API Т-ИНВЕСТИЦИЙ: {e.details}")
        except Exception as e:
            logger.exception(
                f"Критическая ошибка сети при проверке токена: {e}"
            )
            raise ValidationError(
                f"НЕ УДАЛОСЬ УСТАНОВИТЬ СОЕДИНЕНИЕ С СЕРВЕРОМ Т-ИНВЕСТИЦИЙ. Детальная информация ошибки {e}"
            )

    imported_accounts = []
    skipped_accounts = []

    for account in accounts_list:
        try:
            obj, created = await TInvestAccount.objects.aget_or_create(
                account_id=account.id,
                defaults={
                    "user": user,
                    "access_token": invest_token,
                    "description": account.name,
                    "type": int(account.type),
                    "status": int(account.status),
                    "access_level": int(account.access_level),
                    "opened_date": account.opened_date
                    if hasattr(account, "opened_date")
                    else timezone.now(),
                    "closed_date": account.closed_date
                    if hasattr(account, "closed_date")
                    else None,
                },
            )

            if created:
                imported_accounts.append(account.name)
                logger.info(
                    f"Добавлен новый аккаунт {account.id} для пользователя {user.id}"
                )
            else:
                skipped_accounts.append(account.name)
                logger.info(
                    f"Аккаунт {account.id} уже существует у пользователя {user.id}"
                )

        except Exception as e:
            logger.exception(
                f"Ошибка при сохранении аккаунта {account.id} в базу данных: {e}"
            )
            raise ValidationError(
                f"ОШИБКА БАЗЫ ДАННЫХ: НЕ УДАЛОСЬ СОХРАНИТЬ СЧЕТ {account.name}."
            )

    # Формируем итоговое строгое текстовое сообщение для вывода в шаблоне
    result_messages = []
    if imported_accounts:
        result_messages.append(
            f"УСПЕШНО ДОБАВЛЕНЫ СЧЕТА: {', '.join(imported_accounts)}"
        )
    if skipped_accounts:
        result_messages.append(
            f"УЖЕ СУЩЕСТВУЮТ В БАЗЕ: {', '.join(skipped_accounts)}"
        )

    return " // ".join(result_messages)
