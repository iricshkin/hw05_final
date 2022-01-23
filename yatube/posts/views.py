from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import (
    get_list_or_404,
    get_object_or_404,
    redirect,
    render,
)

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

POST_PER_PAGE = 10


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница."""
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POST_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    template = "posts/index.html"
    # В словаре context отправляем информацию в шаблон
    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)


def group_posts(request: HttpRequest, slug: str) -> HttpResponse:
    """Страница группы."""
    group = get_object_or_404(Group, slug=slug)
    post_list = get_list_or_404(Post, group=group)
    paginator = Paginator(post_list, POST_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    template = "posts/group_list.html"
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, template, context)


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """Страница профиля."""
    author = get_object_or_404(User, username=username)
    posts_author = author.posts.all()
    following = author.following.all()
    paginator = Paginator(posts_author, POST_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    template = "posts/profile.html"
    context = {
        "author": author,
        "posts_author": posts_author,
        "following": following,
        "page_obj": page_obj,
    }
    return render(request, template, context)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    """Страница записи."""
    post_info = get_object_or_404(Post, pk=post_id)
    author_post = post_info.author_id
    count_author_posts = (
        Post.objects.select_related("author")
        .filter(author_id=author_post)
        .count()
    )
    comments = post_info.comments.all()
    form = CommentForm()
    template = "posts/post_detail.html"
    context = {
        "post_info": post_info,
        "count_author_posts": count_author_posts,
        "form": form,
        "comments": comments,
    }
    return render(request, template, context)


@login_required
def post_create(request: HttpRequest) -> HttpResponse:
    """Создание нового поста."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:profile", username=post.author.username)

    template = "posts/create_post.html"
    context = {
        "form": form,
    }
    return render(request, template, context)


@login_required
def post_edit(request: HttpRequest, post_id: int) -> HttpResponse:
    """Редактирование поста."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id=post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post.pk)

    template = "posts/create_post.html"
    context = {
        "post": post,
        "form": form,
        "is_edit": True,
    }
    return render(request, template, context)


@login_required
def add_comment(request: HttpRequest, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    template = "posts:post_detail"
    return redirect(template, post_id=post.pk)


@login_required
def follow_index(request: HttpRequest) -> HttpResponse:
    """
    Страница всех постов авторов, на которых подписан текущий пользователь.
    """
    follower = get_object_or_404(User, username=request.user)
    author = Follow.objects.filter(user=follower).values("author")
    posts = Post.objects.filter(author__in=author)
    paginator = Paginator(posts, POST_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    template = "posts/follow.html"
    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request: HttpRequest, username: str) -> HttpResponse:
    # Подписаться на автора
    follower = get_object_or_404(User, username=request.user)
    following = get_object_or_404(User, username=username)
    # follow_list = Follow.objects.filter(user=follower).values("author")
    if follower != following:
        # if not Follow.objects.filter(user=follower).exists():
        if follower not in following.follower.all():
            Follow.objects.filter(user=follower).create(
                author=following, user=follower
            )
    posts = Post.objects.filter(author=following)
    paginator = Paginator(posts, POST_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    template = "posts/follow.html"
    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)


@login_required
def profile_unfollow(request: HttpRequest, username: str) -> HttpResponse:
    # Дизлайк, отписка
    follower = get_object_or_404(User, username=request.user)
    following = get_object_or_404(User, username=username)
    if follower not in following.follower.all():
        Follow.objects.filter(author=following, user=follower).delete()
    posts = Post.objects.filter(author=following)
    paginator = Paginator(posts, POST_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    template = "posts/follow.html"
    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)
