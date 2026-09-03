from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

# В Django 6.1 для асинхронности мы импортируем утилиту sync_to_async, 
# так как clean() пока не умеет быть async нативно
from asgiref.sync import sync_to_async

from user.constant import MAX_LENGHT_EMAIL, MAX_LENGHT_USERS


class User(AbstractUser):
    email = models.EmailField(
        verbose_name="e-mail",
        unique=True,
        max_length=MAX_LENGHT_EMAIL,
    )
    username = models.CharField(
        unique=True,
        verbose_name="имя пользователя в системе",
        max_length=MAX_LENGHT_USERS,
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+$",
                message="«Нельзя использовать пробел и символы, кроме . @ + - _».",
            ),
        ],
    )

    class Meta:
        verbose_name = "Пользователь."
        verbose_name_plural = "Пользователи."

    def clean(self):
        if not self.pk and User.objects.exists():
            raise ValidationError(
                "В этой системе может существовать только один пользователь."
            )
        super().clean()

    async def aclean(self):
        # Используем асинхронный метод ORM — aexists()
        if not self.pk and await User.objects.aexists():
            raise ValidationError(
                "В этой системе может существовать только один пользователь."
            )
        
        # Запускаем базовый clean в безопасном для async потоке
        await sync_to_async(super().clean)()

    def save(self, *args, **kwargs):
        self.full_clean()  
        super().save(*args, **kwargs)

    async def asave(self, *args, **kwargs):
        await self.aclean()  
        await super().asave(*args, **kwargs)

    def __str__(self):
        return self.username
