import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.test import AsyncClient
from django.urls import reverse
from django.utils import timezone

from user.models import TInvestAccount

User = get_user_model()


@pytest.fixture
def urls():
    return {
        "list": reverse("user:account_list"),
        "login": reverse("user:login"),
    }


@pytest.fixture
def async_client():
    return AsyncClient()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestAsyncTInvestAccountListView:
    """
    Набор асинхронных тестов для представления AsyncTInvestAccountListView.
    """

    async def test_redirect_to_login_if_anonymous(self, async_client, urls):
        """
        Проверка: Неавторизованный пользователь перенаправляется на login.
        """
        response = await async_client.get(urls["list"])

        # Проверяем код редиректа
        assert response.status_code == 302
        # Так как middleware делает чистый редирект или использует относительный путь:
        assert urls["login"] in response.url

    async def test_list_view_empty_state_authenticated(
        self, async_client, urls
    ):
        """
        Проверка: У пользователя без аккаунтов выводится строгий текст NO_DATA.
        """
        # Безопасно создаем одного пользователя через sync_to_async,
        # чтобы обойти SynchronousOnlyOperation внутри вашего кастомного User.save() -> full_clean()
        user = await sync_to_async(User.objects.create_user)(
            username="test_trader",
            email="trader@example.com",
            password="secure_password_123",
        )

        # 🔥 ИСПОЛЬЗУЕМ ALOGIN ДЛЯ ASYNC_CLIENT (важно для Django 5.x/6.x)
        await async_client.alogin(
            username="test_trader", password="secure_password_123"
        )

        response = await async_client.get(urls["list"])

        assert response.status_code == 200
        assert len(response.context["accounts"]) == 0
        assert "НЕТ ПОДКЛЮЧЕННЫХ СЧЕТОВ" in response.content.decode("utf-8")

    async def test_list_view_displays_only_user_accounts(
        self, async_client, urls
    ):
        """
        Проверка: Отображаются только счета текущего пользователя в правильной сортировке.
        """
        # Помним про синглтон-логику в вашей модели:
        # в вашей системе может существовать только один пользователь,
        # поэтому создавать other_user не нужно (метод clean() модели User выбросит ValidationError)
        user = await sync_to_async(User.objects.create_user)(
            username="test_trader", email="trader@example.com", password="pwd"
        )

        # Создаем счета для этого единственного пользователя
        # Оборачиваем в sync_to_async для стабильности транзакций sqlite в тестах
        await sync_to_async(TInvestAccount.objects.create)(
            user=user,
            account_id="ACC-11111",
            access_token="token_1",
            description="ОСНОВНОЙ БРОКЕРСКИЙ СЧЕТ",
            type=1,
            status=2,
            access_level=1,
            opened_date=timezone.now(),
        )

        await sync_to_async(TInvestAccount.objects.create)(
            user=user,
            account_id="ACC-22222",
            access_token="token_2",
            description="ИНВЕСТКОПИЛКА",
            type=3,
            status=2,
            access_level=1,
            opened_date=timezone.now(),
        )

        await async_client.alogin(username="test_trader", password="pwd")
        response = await async_client.get(urls["list"])

        assert response.status_code == 200

        accounts_in_context = response.context["accounts"]
        assert len(accounts_in_context) == 2

        # Проверяем сортировку от новых к старым (-created_at)
        assert accounts_in_context[0].account_id == "ACC-22222"
        assert accounts_in_context[1].account_id == "ACC-11111"

        content = response.content.decode("utf-8")
        assert "ACC-11111" in content
        assert "ACC-22222" in content
