from django.contrib.auth import views as auth_views
from django.test import TestCase
from django.urls import resolve, reverse

from user import views


class UserURLsTest(TestCase):
    def test_signup_url(self):
        """
        Тестирование URL-паттерна для регистрации пользователя.
        """
        url = reverse("user:signup")
        self.assertEqual(resolve(url).func.view_class, views.SignUpView)
        self.assertEqual(url, "/register/user/signup/")

    def test_password_reset_url(self):
        """
        Тестирование URL-паттерна для сброса пароля.
        """
        url = reverse("user:password_reset")
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordResetView)
        self.assertEqual(url, "/register/user/password_reset/")

    def test_password_reset_done_url(self):
        """
        Тестирование URL-паттерна для завершения сброса пароля.
        """
        url = reverse("user:password_reset_done")
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordResetDoneView)
        self.assertEqual(url, "/register/user/password_reset/done/")

    def test_password_reset_confirm_url(self):
        """
        Тестирование URL-паттерна для подтверждения сброса пароля.
        """
        url = reverse("user:password_reset_confirm", kwargs={"uidb64": "dummy", "token": "dummy"})
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordResetConfirmView)
        self.assertEqual(url, "/register/user/reset/dummy/dummy/")

    def test_password_reset_complete_url(self):
        """
        Тестирование URL-паттерна для завершения сброса пароля.
        """
        url = reverse("user:password_reset_complete")
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordResetCompleteView)
        self.assertEqual(url, "/register/user/reset/done/")

    def test_password_change_url(self):
        """
        Тестирование URL-паттерна для изменения пароля.
        """
        url = reverse("user:password_change")
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordChangeView)
        self.assertEqual(url, "/register/user/password_change/")

    def test_password_change_done_url(self):
        """
        Тестирование URL-паттерна для завершения изменения пароля.
        """
        url = reverse("user:password_change_done")
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordChangeDoneView)
        self.assertEqual(url, "/register/user/password_change/done/")
