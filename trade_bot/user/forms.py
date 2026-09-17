from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class UserCreatForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class TTokenImportForm(forms.Form):
    access_token = forms.CharField(
        label="Токен Т-Инвестиций (API Ключ)",
        widget=forms.PasswordInput(
            render_value=True,
            attrs={
                "placeholder": "Вставьте ваш токен Т-Инвестиций...",
                "class": "form-control",
            },
        ),
        help_text="Токен с доступом к конкретному счету — токен для получения доступа только к одному конкретному счету пользователя.",
        required=True,
    )
