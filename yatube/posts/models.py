from core.models import CreatedModel
from django.contrib.auth import get_user_model
from django.db import models

# from django.db.models import Q

User = get_user_model()


class Group(models.Model):
    title = models.CharField("Наименование", max_length=200)
    slug = models.SlugField("Адрес", unique=True, null=True)
    description = models.TextField("Описание")

    class Meta:
        verbose_name = "Группa"
        verbose_name_plural = "Группы"

    def __str__(self) -> str:
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        "Текст поста",
        help_text="Введите текст поста",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
        verbose_name="Группа",
        help_text="Выберите группу",
    )
    # Поле для картинки (необязательное)
    image = models.ImageField(
        "Картинка",
        upload_to="posts/",
        blank=True,
        help_text="Добавьте картинку",
    )
    # Аргумент upload_to указывает директорию,
    # в которую будут загружаться пользовательские файлы.

    class Meta:
        ordering = (
            "-created",
            "-pk",
        )
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self) -> str:
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Комментируемый пост",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
    )
    text = models.TextField(
        "Текст комментария",
        help_text="Напишите комментарий",
    )

    class Meta:
        ordering = ("-created",)
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self) -> str:
        return self.text[:20]


class Follow(CreatedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Избранный автор",
    )

    class Meta:
        ordering = ("-created",)
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = ("author", "user")

    def __str__(self) -> str:
        return f"{self.user} подписан на {self.author}"
