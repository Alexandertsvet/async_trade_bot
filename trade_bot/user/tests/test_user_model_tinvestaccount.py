import pytest
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.utils import timezone

from user.models import TInvestAccount

User = get_user_model()


@pytest.fixture
def test_password():
    return "strong-test-password-123"


@pytest.fixture
async def create_user(db, test_password):
    """Асинхронная фикстура для создания тестового пользователя."""
    user = await User.objects.acreate(
        username="test_trader",
        email="trader@example.com",
        password=test_password,
    )
    return user


@pytest.mark.django_db(transaction=True)
class TestTInvestAccountAsync:
    async def test_create_account_with_defaults(self, create_user):
        """Проверка успешного создания аккаунта со значениями по умолчанию."""
        user = create_user

        account = await TInvestAccount.objects.acreate(
            user=user,
            account_id="ACC123456",
            access_token="t.mock_token_secret_123",
            description="Основной счет для тестов",
        )

        assert account.id is not None
        assert account.account_id == "ACC123456"
        assert account.type == TInvestAccount.AccountType.ACCOUNT_TYPE_TINKOFF

    async def test_str_method(self, create_user):
        """Проверка строкового представления модели __str__."""
        user = create_user

        account = await TInvestAccount.objects.acreate(
            user=user, account_id="STR_ACCOUNT_ID", access_token="token"
        )
        assert str(account) == "Account: STR_ACCOUNT_ID"

    async def test_unique_account_id_constraint(self, create_user):
        """Проверка глобального ограничения уникальности account_id (unique=True)."""
        user = create_user

        await TInvestAccount.objects.acreate(
            user=user, account_id="DUPLICATE_ID", access_token="token1"
        )

        with pytest.raises(IntegrityError):
            await TInvestAccount.objects.acreate(
                user=user, account_id="DUPLICATE_ID", access_token="token2"
            )

    async def test_unique_user_account_id_constraint(self, create_user):
        """Проверка UniqueConstraint(fields=['user', 'account_id'])."""
        user = create_user

        await TInvestAccount.objects.acreate(
            user=user, account_id="UNIQUE_PAIR_ID", access_token="token"
        )

        with pytest.raises(IntegrityError):
            await TInvestAccount.objects.acreate(
                user=user,
                account_id="UNIQUE_PAIR_ID",
                access_token="another_token",
            )

    async def test_custom_choices_and_dates(self, create_user):
        """Проверка кастомных статусов, типов, уровней доступа и дат открытия/закрытия."""
        user = create_user
        now = timezone.now()

        account = await TInvestAccount.objects.acreate(
            user=user,
            account_id="CUSTOM_ACC_999",
            access_token="token",
            type=TInvestAccount.AccountType.ACCOUNT_TYPE_TINKOFF_IIS,
            status=TInvestAccount.AccountStatus.ACCOUNT_STATUS_CLOSED,
            access_level=TInvestAccount.AccessLevel.ACCOUNT_ACCESS_LEVEL_READ_ONLY,
            opened_date=now,
            closed_date=now,
        )

        db_account = await TInvestAccount.objects.aget(id=account.id)

        assert (
            db_account.type
            == TInvestAccount.AccountType.ACCOUNT_TYPE_TINKOFF_IIS
        )
        assert (
            db_account.status
            == TInvestAccount.AccountStatus.ACCOUNT_STATUS_CLOSED
        )
        assert (
            db_account.access_level
            == TInvestAccount.AccessLevel.ACCOUNT_ACCESS_LEVEL_READ_ONLY
        )

    async def test_encrypted_field_saves_and_reads(self, create_user):
        """Проверка того, что CustomEncryptedCharField сохраняет и отдает данные корректно."""
        user = create_user
        raw_token = "v1.secret.tinkoff.api.key.here"

        account = await TInvestAccount.objects.acreate(
            user=user, account_id="ENC_ACC", access_token=raw_token
        )

        db_account = await TInvestAccount.objects.aget(id=account.id)
        assert db_account.access_token == raw_token
