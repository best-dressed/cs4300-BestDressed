from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Count, Max
from .models import Thread, Post
from .forms import ThreadForm, PostForm

# Create your views here.
@login_required
def post_delete(request, post_id):
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

def threads(request):
    all_threads = Thread.objects.all().order_by('-created_at')  # newest first
    return render(request, 'forum/threads.html', {'threads': all_threads})



@login_required
def thread_create(request):
    """Create a new thread without creating an initial post."""
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.user = request.user
            thread.save()
            return redirect('thread_detail', thread_id=thread.id)
    else:
        form = ThreadForm()
    return render(request, 'forum/thread_form.html', {'form': form, 'creating': True})

@login_required
def thread_edit(request, thread_id):
    """Edit a thread. Only the thread author may edit (adjust permission as needed)."""
    thread = get_object_or_404(Thread, id=thread_id)

    if not(request.user == thread.user or request.user.is_staff):
        messages.error(request, "You don't have permission to edit this thread.")
        return redirect('thread_detail', thread_id=thread.id)

    if request.method == 'POST':
        form = ThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            messages.success(request, "Thread updated.")
            return redirect('thread_detail', thread_id=thread.id)
    else:
        form = ThreadForm(instance=thread)

    return render(request, 'forum/thread_form.html', {
        'form': form,
        'creating': False,
        'thread': thread,
    })

@login_required
def thread_delete(request, thread_id):
    """
    Delete a thread. Only the thread owner or a staff user may delete.
    This view expects POST requests (protects against accidental GET deletes).
    """
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

def thread_detail(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    posts = thread.posts.select_related('user').order_by('created_at')
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        form = PostForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.thread, p.user = thread, request.user
            p.save()
            return redirect('thread_detail', thread_id=thread.id)
    else:
        form = PostForm()
    return render(request, 'forum/thread_detail.html', {'thread': thread, 'posts': posts, 'form': form})

@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # only author or staff can delete
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