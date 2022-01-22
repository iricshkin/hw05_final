from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls.base import reverse
from django import forms

User = get_user_model()


class UserURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username="leo")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            "users/signup.html": reverse("users:signup"),
            "users/login.html": reverse("users:login"),
            "users/password_change_form.html": reverse(
                "users:password_change"
            ),
            "users/password_change_done.html": reverse(
                "users:password_change_done"
            ),
            "users/password_reset_form.html": reverse(
                "users:password_reset_form"
            ),
            "users/password_reset_done.html": reverse(
                "users:password_reset_done"
            ),
            "users/password_reset_confirm.html": reverse(
                "users:password_reset_confirm", args=("uid64", "token")
            ),
            "users/password_reset_complete.html": reverse(
                "users:password_reset_complete"
            ),
            "users/logged_out.html": reverse("users:logout"),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_signup_pages_show_correct_context(self):
        """Шаблон signup передается форма для создания нового пользователя."""
        response = self.guest_client.get(reverse("users:signup"))
        form_fields = {
            "first_name": forms.fields.CharField,
            "last_name": forms.fields.CharField,
            "username": forms.fields.CharField,
            "email": forms.fields.EmailField,
        }
        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)
