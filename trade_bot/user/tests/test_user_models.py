import pytest
from asgiref.sync import sync_to_async
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TransactionTestCase

from user.models import TInvestAccount, User
from user.module_encrypted_field import CustomEncryptedCharField

User = get_user_model()


class UserModelTest(TransactionTestCase):
    @pytest.mark.asyncio
    async def test_unique_user(self):
        """
        Тестирование создания уникального пользователя.
        """
        await User.objects.acreate(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",
        )
        with pytest.raises(ValidationError):
            await User.objects.acreate(
                username="testuser",
                email="anotheruser@example.com",
                password="anotherpassword",
            )

    @pytest.mark.asyncio
    async def test_valid_username(self):
        """
        Тестирование валидации корректного имени пользователя.
        """
        user = User(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",
        )
        await sync_to_async(user.full_clean)()


class AccountModelTest(TransactionTestCase):
    @pytest.mark.asyncio
    async def test_user_user_access_token(self):
        user = await User.objects.acreate(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",
        )
        account = await TInvestAccount.objects.acreate(
            user=user,
            account_id="test_account_id",
            access_token="test_access_token",
            description="Test Description",
        )
        fernet = Fernet(settings.FIELD_ENCRYPTION_KEY)
        encrypted_token_1 = fernet.encrypt(
            "test_access_token".encode("utf-8")
        ).decode("utf-8")
        encrypted_token_2 = fernet.encrypt(
            "test_access_token".encode("utf-8")
        ).decode("utf-8")

        decrypted_token_1 = fernet.decrypt(
            encrypted_token_1.encode("utf-8")
        ).decode("utf-8")
        decrypted_token_2 = fernet.decrypt(
            encrypted_token_2.encode("utf-8")
        ).decode("utf-8")

        self.assertNotEqual(decrypted_token_1, encrypted_token_1)
        self.assertNotEqual(decrypted_token_2, encrypted_token_2)
        self.assertNotEqual(encrypted_token_1, encrypted_token_2)
        self.assertEqual(decrypted_token_1, "test_access_token")
        self.assertEqual(decrypted_token_2, "test_access_token")
        self.assertEqual(decrypted_token_1, decrypted_token_2)
        self.assertIsNotNone(account.created_at)
        self.assertIsNotNone(account.updated_at)
        self.assertEqual(account.access_token, "test_access_token")


class CustomEncryptedCharFieldTest(TransactionTestCase):
    def test_encryption_and_decryption(self):
        """
        Тестирование шифрования и дешифрования CustomEncryptedCharField.
        """
        field = CustomEncryptedCharField(max_length=512)
        value = "test_value"
        encrypted_value = field.get_prep_value(value)
        decrypted_value = field.from_db_value(encrypted_value, None, None)
        self.assertEqual(decrypted_value, value)
