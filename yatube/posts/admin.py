from django.contrib import admin

from .models import Comment, Group, Post


class PostAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = ("pk", "text", "created", "author", "group")
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


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Comment, CommentAdmin)
