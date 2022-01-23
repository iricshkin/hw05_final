from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = (
        "pk",
        "text",
        "created",
        "author",
        "group",
        "image",
    )
    # Добавляем интерфейс для изменений поля group
    list_editable = ("group",)
    # Добавляем интерфейс для поиска по тексту постов
    search_fields = ("text",)
    # Добавляем возможность фильтрации по дате
    list_filter = ("created",)
    # Это свойство сработает для всех колонок: где пусто — там будет эта строка
    empty_value_display = "-пусто-"


class CommentAdmin(admin.ModelAdmin):
    list_display = ("pk", "post", "text", "created", "author")
    list_filter = ("created",)
    search_fields = ("text",)


class FollowAdmin(admin.ModelAdmin):
    list_display = ("user", "author")
    list_filter = ("user",)
    search_fields = ("user",)


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Comment)
admin.site.register(Follow, FollowAdmin)
