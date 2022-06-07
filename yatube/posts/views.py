from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

POST_PER_PAGE = 10


class PostHome(ListView):
    """Главная страница."""

    paginate_by = POST_PER_PAGE
    model = Post
    template_name = "posts/index.html"
    context_object_name = "posts"

    def get_queryset(self):
        return Post.objects.all()


class GroupPosts(ListView):
    """Страница группы."""

    paginate_by = POST_PER_PAGE
    model = Group
    template_name = "posts/group_list.html"
    context_object_name = "posts"

    def get_queryset(self):
        group = get_object_or_404(Group, slug=self.kwargs["slug"])
        return Post.objects.filter(group=group)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = str(context["posts"][0].group)
        context["description"] = context["posts"][0].group.description
        return context


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """Страница профиля."""
    author = get_object_or_404(User, username=username)
    posts_author = author.posts.all()
    following = author.following.all().exists()
    paginator = Paginator(posts_author, POST_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    template = "posts/profile.html"
    context = {
        "author": author,
        "posts_author": posts_author,
        "page_obj": page_obj,
        "following": following,
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
    posts = Post.objects.filter(author__following__user=request.user)
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
    current_user = request.user
    author = get_object_or_404(User, username=username)
    if author != current_user:
        Follow.objects.get_or_create(user=current_user, author=author)
        return redirect("posts:profile", username=username)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def profile_unfollow(request: HttpRequest, username: str) -> HttpResponse:
    # Дизлайк, отписка
    current_user = request.user
    Follow.objects.filter(
        user=current_user, author__username=username
    ).delete()
    return redirect("posts:profile", username=username)
