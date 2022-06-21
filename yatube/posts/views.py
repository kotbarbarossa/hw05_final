
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

posts_limit: int = 10


@cache_page(20, key_prefix="index_page")
def index(request):
    """Функция выводит информаницю на станицу index.html."""
    post_list = Post.objects.select_related('author').all()
    template = 'posts/index.html'
    paginator = Paginator(post_list, posts_limit)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request):
    """Функция выводит информаницю на станицу group.html."""
    template = 'posts/group.html'
    context = {
    }
    return render(request, template, context)


def group_posts_list(request, slug):
    """Функция выводит информаницю на станицу group_list.html."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    template = 'posts/group_list.html'
    paginator = Paginator(post_list, posts_limit)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'slug': slug,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.author.select_related(
        'author')
    template = 'posts/profile.html'
    paginator = Paginator(post_list, posts_limit)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    user = request.user
    following = (
        user.is_authenticated and Follow.objects.filter(
            user=user, author=author
        ).exists()
    )

    context = {
        'username': username,
        'page_obj': page_obj,
        'post_list': post_list,
        'author': author,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = Post.objects.get(pk=post_id)
    username = post.author
    post_list = Post.objects.select_related(
        'author').filter(author__username=username)
    comments = post.comments.select_related(
        'author')
    template = 'posts/post_detail.html'
    context = {
        'title': post.text[:30],
        'post': post,
        'post_list': post_list,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None,
                        files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user)
    template = 'posts/create_post.html'
    context = {
        'form': PostForm(),
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.pk = post_id
        post.pub_date = Post.objects.get(pk=post_id).pub_date
        post.save()
        return redirect('posts:post_detail', post_id=post.pk)

    template = 'posts/create_post.html'
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST or None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    template = 'posts/post_detail.html'
    post = Post.objects.get(pk=post_id)
    username = post.author
    post_list = Post.objects.select_related(
        'author').filter(author__username=username)
    comments = post.comments.select_related(
        'author')
    context = {
        'title': post.text[:30],
        'post': post,
        'post_list': post_list,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    template = 'posts/follow.html'
    paginator = Paginator(post_list, posts_limit)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follower = Follow.objects.get(user=user, author=author)
        Follower.delete()
    return redirect('posts:profile', username=username)
