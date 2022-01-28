from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls.base import reverse_lazy

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text="Текст поста",
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username="leo")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Авторизируем автора поста
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    # Проверяем общедоступные страницы
    def test_pages_url_exists_at_desired_location(self):
        """
        Страницы /, /group/slug/, /profile/username/, /posts/post_id/
        доступны любому пользователю.
        """
        url_names = (
            reverse_lazy("posts:index"),
            reverse_lazy("posts:group_list", kwargs={"slug": self.group.slug}),
            reverse_lazy(
                "posts:profile", kwargs={"username": self.user.username}
            ),
            reverse_lazy(
                "posts:post_detail", kwargs={"post_id": self.post.pk}
            ),
        )
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_error_page_url_exists_at_desired_location(self):
        """Запрос к несуществующей странице вернет ошибку 404."""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        """URL-адрес использует соответствующий шаблон."""
        self.assertTemplateUsed(response, "core/404.html")

    # Проверяем доступность страниц для авторизованного пользователя
    def test_post_url_exists_at_desired_location_authorized(self):
        """
        Страницы create/, posts/<int:post_id>/comment, follow/ доступны
        авторизованному пользователю.
        """
        url_names = (
            reverse_lazy("posts:post_create"),
            reverse_lazy("posts:follow_index"),
        )
        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем доступность страниц для авторизованного автора поста
    def test_post_url_exists_at_post_author_authorized(self):
        """
        Страница posts/<post_id>/edit/ доступна авторизованному автору поста.
        """
        url = reverse_lazy("posts:post_edit", kwargs={"post_id": self.post.pk})
        response = self.authorized_author.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names_template = {
            reverse_lazy("posts:index"): "posts/index.html",
            reverse_lazy(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse_lazy(
                "posts:profile", kwargs={"username": self.user.username}
            ): "posts/profile.html",
            reverse_lazy(
                "posts:post_detail", kwargs={"post_id": self.post.pk}
            ): "posts/post_detail.html",
            reverse_lazy("posts:post_create"): "posts/create_post.html",
            reverse_lazy("posts:follow_index"): "posts/follow.html",
        }
        for url, template in url_names_template.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_post_edit_uses_correct_template(self):
        """URL-адрес post_edit использует соответствующий шаблон."""
        url = reverse_lazy("posts:post_edit", kwargs={"post_id": self.post.pk})
        template = "posts/create_post.html"
        response = self.authorized_author.get(url)
        self.assertTemplateUsed(response, template)
