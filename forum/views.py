"""Views for the forum app."""
# pylint: disable=too-few-public-methods,no-member
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Count
# from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from moderation.moderation_common import (
    content_filter_decorator,
    unbanned_ip_and_login,
    poster_not_ip_banned
)
from .models import Thread, Post, ThreadLike, PostLike, SavedThread
from .forms import ThreadForm, PostForm


def create_validator(form_class):
    """Create a validator that only checks for field errors."""
    def validator(request):
        form = form_class(request.POST)
        if form.is_valid():
            return True
        # Act normal if they aren't field errors
        return not any(name not in request.POST for name in form.fields)
    return validator


thread_content_filter_decorator = content_filter_decorator(
    lambda request: request.POST['title'],  # filter the title
    lambda request: request.POST['content'],  # filter the content
    validator=create_validator(ThreadForm)
)

post_content_filter_decorator = content_filter_decorator(
    lambda request: request.POST['content'],  # filter the content
    validator=create_validator(PostForm)
)


@login_required
def post_delete(request, post_id):
    """Delete a post. Only author or staff can delete."""
    post = get_object_or_404(Post.objects.select_related('thread', 'user'), id=post_id)
    # only author or staff can delete
    if not (request.user == post.user or request.user.is_staff):
        return redirect('thread_detail', thread_id=post.thread.id)

    if request.method == 'POST':
        thread_id = post.thread.id
        post.delete()
        return redirect('thread_detail', thread_id=thread_id)

    # GET -> show confirmation page
    return redirect('thread_detail', thread_id=post.thread.id)


def threads_list(request):
    """Display list of all threads."""
    # Annotate with reply count
    all_threads = Thread.objects.annotate(
        reply_count=Count('posts')
    ).order_by('-created_at')

    # Add is_saved_by info for each thread
    if request.user.is_authenticated:
        for thread in all_threads:
            thread.is_saved_by = thread.is_saved_by(request.user)

    return render(request, 'forum/threads.html', {'threads': all_threads})


@unbanned_ip_and_login
@thread_content_filter_decorator
@login_required
def thread_create(request):
    """Create a new thread."""
    if request.method == 'POST':
        form = ThreadForm(request.POST, user=request.user)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.user = request.user
            thread.save()
            return redirect('thread_detail', thread_id=thread.id)
    else:
        form = ThreadForm(user=request.user)
    return render(request, 'forum/thread_form.html', {'form': form, 'creating': True})


@unbanned_ip_and_login
@thread_content_filter_decorator
@login_required
def thread_edit(request, thread_id):
    """Edit a thread. Only the thread author or staff may edit."""
    thread = get_object_or_404(Thread, id=thread_id)

    if not (request.user == thread.user or request.user.is_staff):
        messages.error(request, "You don't have permission to edit this thread.")
        return redirect('thread_detail', thread_id=thread.id)

    if request.method == 'POST':
        form = ThreadForm(request.POST, instance=thread, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Thread updated.")
            return redirect('thread_detail', thread_id=thread.id)
    else:
        form = ThreadForm(instance=thread, user=request.user)

    return render(request, 'forum/thread_form.html', {
        'form': form,
        'creating': False,
        'thread': thread,
    })


@login_required
def thread_delete(request, thread_id):
    """Delete a thread. Only the thread owner or staff may delete."""
    thread = get_object_or_404(Thread, id=thread_id)

    # permission check: owner or staff/superuser
    if not (request.user == thread.user or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to delete this thread.")
        return redirect('thread_detail', thread_id=thread.id)

    if request.method == 'POST':
        thread.delete()
        messages.success(request, "Thread deleted.")
        return redirect('threads')

    # If a GET sneaks through, redirect to detail (we only accept POST deletes)
    return redirect('thread_detail', thread_id=thread.id)


@poster_not_ip_banned
@post_content_filter_decorator
def thread_detail(request, thread_id):
    """Display thread detail with posts and allow posting."""
    thread = get_object_or_404(Thread, id=thread_id)
    posts = thread.posts.select_related('user').order_by('created_at')
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread, post.user = thread, request.user
            post.save()
            return redirect('thread_detail', thread_id=thread.id)
    else:
        form = PostForm()
    return render(request, 'forum/thread_detail.html', {
        'thread': thread,
        'posts': posts,
        'form': form
    })


@unbanned_ip_and_login
@post_content_filter_decorator
def post_edit(request, post_id):
    """Edit a post. Only author or staff can edit."""
    post = get_object_or_404(Post, id=post_id)
    # only author or staff can edit
    if not (request.user == post.user or request.user.is_staff):
        return redirect('thread_detail', thread_id=post.thread.id)

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('thread_detail', thread_id=post.thread.id)
    else:
        form = PostForm(instance=post)

    return render(request, 'forum/post_edit.html', {'form': form, 'post': post})


@login_required
@require_POST
def toggle_thread_like(request, thread_id):
    """Toggle like status on a thread."""
    thread = get_object_or_404(Thread, id=thread_id)
    like, created = ThreadLike.objects.get_or_create(thread=thread, user=request.user)

    if not created:
        # Unlike if already liked
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked': liked,
        'like_count': thread.like_count()
    })


@login_required
@require_POST
def toggle_post_like(request, post_id):
    """Toggle like status on a post."""
    post = get_object_or_404(Post, id=post_id)
    like, created = PostLike.objects.get_or_create(post=post, user=request.user)

    if not created:
        # Unlike if already liked
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked': liked,
        'like_count': post.like_count()
    })


@login_required
@require_POST
def toggle_thread_save(request, thread_id):
    """Toggle save status on a thread."""
    thread = get_object_or_404(Thread, id=thread_id)
    saved, created = SavedThread.objects.get_or_create(thread=thread, user=request.user)

    if not created:
        # Unsave if already saved
        saved.delete()
        is_saved = False
    else:
        is_saved = True

    return JsonResponse({
        'saved': is_saved
    })


@login_required
def my_saved_threads(request):
    """Display user's saved threads."""
    saved = SavedThread.objects.filter(
        user=request.user
    ).select_related('thread', 'thread__user').order_by('-saved_at')
    thread_list = [s.thread for s in saved]

    # Add reply count for each thread
    for thread in thread_list:
        thread.reply_count = thread.posts.count()
        thread.is_saved_by = True  # Already saved since we're on saved page

    return render(request, 'forum/saved_threads.html', {'threads': thread_list})
