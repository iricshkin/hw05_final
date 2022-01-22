from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserFormTests(TestCase):
    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    def test_signup(self):
        """Валидная форма создает запись в User."""
        users_count = User.objects.count()
        user_data = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "username": "testuser",
            "email": "testuser@gmail.com",
            "password1": "Parol123",
            "password2": "Parol123",
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse("users:signup"),
            data=user_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse("posts:index"))
        # Проверяем, увеличилось ли число пользователей
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(
                username="testuser",
            ).exists()
        )
