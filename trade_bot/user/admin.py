from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Регистрируем кастомного пользователя со стандартным поведением админки
admin.site.register(User, UserAdmin)