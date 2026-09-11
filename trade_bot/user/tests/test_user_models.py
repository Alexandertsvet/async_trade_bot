import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from user.models import User

User = get_user_model()


class UserModelTest(TestCase):
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
        user = User(username="testuser", email="testuser@example.com", password="testpassword")
        await sync_to_async(user.full_clean)()
