from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls.base import reverse

User = get_user_model()


class UserURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username="leo")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем общедоступные страницы
    def test_signup_and_login_url_exists_at_desired_location(self):
        """
        Страницы /auth/signup/, /auth/login/ доступны любому пользователю.
        """
        url_names = {
            reverse("users:signup"),
            reverse("users:login"),
        }
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_users_url_exists_at_desired_location_authorized(self):
        """
        Страницы /auth/logout/, /auth/password_change/,
        /auth/password_change/done/, /auth/password_change/done/,
        /auth/password_reset/, /auth/password_reset/done/,
        /auth/reset/<uidb64>/<token>/, /auth/reset/done/ доступны
        авторизованному пользователю.
        """
        url_names = {
            reverse("users:password_change"),
            reverse("users:password_change_done"),
            reverse("users:password_reset_form"),
            reverse("users:password_reset_done"),
            reverse("users:password_reset_confirm", args=["uidb64", "token"]),
            reverse("users:password_reset_complete"),
        }
        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_url_exists_at_desired_location_authorized(self):
        """Страница /auth/logout/ доступна авторизированному пользователю."""
        response = self.authorized_client.get(
            reverse("users:logout"),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names_template = {
            reverse("users:signup"): "users/signup.html",
            reverse("users:login"): "users/login.html",
            reverse(
                "users:password_change"
            ): "users/password_change_form.html",
            reverse(
                "users:password_change_done"
            ): "users/password_change_done.html",
            reverse(
                "users:password_reset_form"
            ): "users/password_reset_form.html",
            reverse(
                "users:password_reset_done"
            ): "users/password_reset_done.html",
            reverse(
                "users:password_reset_confirm", args=["uidb64", "token"]
            ): "users/password_reset_confirm.html",
            reverse(
                "users:password_reset_complete"
            ): "users/password_reset_complete.html",
            reverse("users:logout"): "users/logged_out.html",
        }
        for url, template in url_names_template.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
