import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="leo")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Текст поста",
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Посчитаем количество записей
        posts_count = Post.objects.count()
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif",
        )
        form_data = {
            "text": "Текст поста new",
            "image": uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": self.user.username}),
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Текст поста new",
                image="posts/small.gif",
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        # Посчитаем количество записей
        posts_count = Post.objects.count()
        # Редактируем созданный пост
        form_data = {
            "text": "Текст поста change",
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True,
        )
        # Убедимся, что запись в базе данных не создалась
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk}),
        )
        self.assertTrue(
            Post.objects.filter(
                text="Текст поста change",
            ).exists()
        )

    def test_cant_create_without_text(self):
        posts_count = Post.objects.count()
        form_data = {
            "text": "",
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response,
            "form",
            "text",
            "Обязательное поле.",
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="leo")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Текст поста",
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text="Комментарий",
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment_post(self):
        """Валидная форма создает запись в Comment."""
        # Посчитаем количество записей
        comments_count = Comment.objects.count()
        form_data = {
            "text": "Комментарий new",
        }
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True,
        )
        # Убедимся, что запись в базе данных создалась
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk}),
        )
        self.assertTrue(
            Comment.objects.filter(
                text="Комментарий new",
            ).exists()
        )

    def test_not_add_comment_post_guest_client(self):
        """
        Неавторизированный пользователь не может создать запись в Comment.
        """
        # Посчитаем количество записей
        comments_count = Comment.objects.count()
        form_data = {
            "text": "Комментарий new",
        }
        response = self.guest_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True,
        )
        # Убедимся, что запись в базе данных не создалась
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(
            Comment.objects.filter(
                text="Комментарий new",
            ).exists()
        )
