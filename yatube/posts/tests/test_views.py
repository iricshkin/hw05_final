import shutil
import tempfile
from itertools import islice

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

NUMBER_OF_POSTS = 14


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username="user_1")
        cls.user_2 = User.objects.create_user(username="user_2")
        cls.group_1 = Group.objects.create(
            title="Первая тестовая группа",
            slug="test-slug-1",
            description="Тестовое описание первой группы",
        )
        cls.group_2 = Group.objects.create(
            title="Вторая тестовая группа",
            slug="test-slug-2",
            description="Тестовое описание второй группы",
        )
        cls.post_1 = (
            Post(
                author=cls.user_1,
                text="Текст поста %s" % post_num,
                group=cls.group_1,
            )
            for post_num in range(1, NUMBER_OF_POSTS)
        )
        batch_size = 14
        Post.objects.bulk_create(list(islice(cls.post_1, batch_size)))
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
        cls.post_2 = (
            Post(
                author=cls.user_2,
                text="Текст поста %s" % post_num,
                group=cls.group_2,
                image=uploaded,
            )
            for post_num in range(NUMBER_OF_POSTS, NUMBER_OF_POSTS + 1)
        )
        Post.objects.bulk_create(list(islice(cls.post_2, batch_size)))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
            reverse("posts:index"): "posts/index.html",
            reverse("posts:group_list", kwargs={"slug": self.group_1.slug}): (
                "posts/group_list.html"
            ),
            reverse(
                "posts:profile", kwargs={"username": self.user_1.username}
            ): ("posts/profile.html"),
            reverse("posts:post_detail", kwargs={"post_id": "1"}): (
                "posts/post_detail.html"
            ),
            reverse("posts:post_edit", kwargs={"post_id": "1"}): (
                "posts/create_post.html"
            ),
            reverse("posts:post_create"): "posts/create_post.html",
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse("posts:index"))
        first_object = response.context["page_obj"][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, "Текст поста 14")

    def test_first_page_index_contains_ten_records(self):
        response = self.guest_client.get(reverse("posts:index"))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_page_index_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.guest_client.get(reverse("posts:index") + '?page=2')
        self.assertEqual(len(response.context["page_obj"]), 4)

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group_1.slug})
        )
        self.assertEqual(
            response.context["group"].title, "Первая тестовая группа"
        )
        self.assertEqual(response.context["group"].slug, self.group_1.slug)
        self.assertEqual(
            response.context["group"].description,
            "Тестовое описание первой группы",
        )

    def test_first_page_group_list_contains_ten_records(self):
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group_1.slug})
        )
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_page_group_list_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group_1.slug})
            + '?page=2'
        )
        self.assertEqual(len(response.context["page_obj"]), 3)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse("posts:profile", kwargs={"username": self.user_1.username})
        )
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context["page_obj"][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, "Текст поста 13")
        self.assertEqual(post_author_0, self.user_1.username)

    def test_first_page_profile_contains_ten_records(self):
        response = self.guest_client.get(
            reverse("posts:profile", kwargs={"username": self.user_1.username})
        )
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_page_profile_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.guest_client.get(
            reverse("posts:profile", kwargs={"username": self.user_1.username})
            + '?page=2'
        )
        self.assertEqual(len(response.context["page_obj"]), 3)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": "1"})
        )
        self.assertTrue(
            Post.objects.filter(
                pk="1",
            ).exists()
        )
        self.assertEqual(response.context["post_info"].text, "Текст поста 1")

    def test_create_post_pages_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }
        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_edit_post_pages_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": "1"})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }
        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)
        self.assertTrue(
            Post.objects.filter(
                pk="1",
            ).exists()
        )

    def test_post_with_group_and_image_show_prodile_pages(self):
        """
        Новый пост с указанной группой и картинкой попадает страницу профайла.
        """
        response = self.guest_client.get(
            reverse("posts:profile", kwargs={"username": self.user_2.username})
        )
        first_object = response.context["page_obj"][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_image_0 = first_object.image.name
        self.assertEqual(post_text_0, "Текст поста 14")
        self.assertEqual(post_author_0, self.user_2.username)
        self.assertEqual(post_image_0, "posts/small.gif")

    def test_post_with_group_and_image_show_group_pages(self):
        """
        Новый пост с указанной группой и картинкой попадает на страницу
        выбранной группы.
        """
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group_2.slug})
        )
        first_object = response.context["page_obj"][0]
        post_group_0 = first_object.group.title
        post_image_0 = first_object.image.name
        self.assertEqual(post_group_0, "Вторая тестовая группа")
        self.assertIsNot(post_group_0, "Первая тестовая группа")
        self.assertEqual(post_image_0, "posts/small.gif")

    def test_post_with_group_and_image_show_post_detail_pages(self):
        """
        Новый пост с указанной группой и картинкой попадает на страницу
        выбранного поста.
        """
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": "14"})
        )
        post = response.context["post_info"]
        post_group = post.group.title
        post_image = post.image.name
        self.assertEqual(post_group, "Вторая тестовая группа")
        self.assertEqual(post_image, "posts/small.gif")


class CommentViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
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

    def test_add_comment_post(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse("posts:add_comment", kwargs={"post_id": self.post.pk})
        )
        self.assertTrue(
            Comment.objects.filter(
                text="Комментарий",
            ).exists()
        )
        self.assertEqual(response.text, self.comment.text)


class PostCacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.post = Post.objects.create(
            author=cls.user,
            text="Текст поста",
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    def test_index_cached(self):
        """Тест работы кэширования главной страницы."""
        posts_count = Post.objects.count()
        response = self.guest_client.get(reverse("posts:index"))
        cache_content = response.content
        self.assertEqual(Post.objects.count(), posts_count)
        self.post.delete()
        response = self.guest_client.get(reverse("posts:index"))
        self.assertEqual(Post.objects.count(), posts_count - 1)
        self.assertIn(cache_content, response.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.following = User.objects.create_user(username="following")
        cls.unfollowing = User.objects.create_user(username="unfollowing")

    def setUp(self):
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_auth_follow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять подписки.
        """
        self.authorized_client.get(
            reverse("posts:profile_follow"),
            kwargs={"username": self.following},
        )
        self.assertIs(
            Follow.objects.filter(
                user=self.user, author=self.following
            ).exists(),
            True,
        )
        self.authorized_client.get(
            reverse("posts:profile_follow"),
            kwargs={"username": self.following.username},
        )
        self.assertIs(
            Follow.objects.filter(
                user=self.user, author=self.following
            ).exists(),
            False,
        )

    def test_new_post_following_author(self):
        """Новая запись пользователя будет в ленте у тех кто на него
        подписан и не будет у тех кто не подписан на него.
        """
        Follow.objects.create(user=self.user, author=self.following)
        post = Post.objects.create(author=self.following, text="New text")
        response = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertIn(post, response.context["page_obj"][0])
        self.client.login(username=self.unfollowing)
        response = self.aclient.get(reverse("posts:follow_index"))
        self.assertNotIn(post, response.context["page_obj"][0])
