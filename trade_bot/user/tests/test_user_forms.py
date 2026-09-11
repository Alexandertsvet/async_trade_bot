from django.test import TestCase

from user.forms import UserCreatForm


class UserFormTest(TestCase):
    def test_form_fields(self):
        """
        Тестирование полей формы UserCreatForm.
        """
        form = UserCreatForm()
        expected_fields = ["username", "email", "password1", "password2"]
        self.assertEqual(list(form.fields), expected_fields)

    def test_form_valid(self):
        """
        Тестирование валидации формы UserCreatForm.
        """
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password1": "testpassword",
            "password2": "testpassword",
        }
        form = UserCreatForm(data)
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        """
        Тестирование невалидации формы UserCreatForm.
        """
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password1": "testpassword",
            "password2": "wrongpassword",
        }
        form = UserCreatForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
