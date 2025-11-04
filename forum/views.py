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
def create_post(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = thread
            post.user = request.user
            post.save()
            return redirect('thread_detail', thread_id=thread.id)
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form, 'thread': thread})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    thread_id = post.thread.id
    if request.user == post.user:
        post.delete()
    return redirect('thread_detail', thread_id=thread_id)

def threads(request):
    all_threads = Thread.objects.all().order_by('-created_at')  # newest first
    return render(request, '../forum/threads.html', {'threads': all_threads})


def thread_detail(request, thread_id):
    """
    Show a single thread and its posts. Handle posting a reply via POST.
    """
    thread = get_object_or_404(Thread, id=thread_id)
    posts = Post.objects.filter(thread=thread).select_related('user').order_by('created_at')

    # Reply form (must be POST and authenticated)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "You must be signed in to reply.")
            return redirect('thread_detail', thread_id=thread.id)

        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = thread
            post.user = request.user
            post.save()
            messages.success(request, "Reply posted.")
            return redirect('thread_detail', thread_id=thread.id)
    else:
        form = PostForm()

    context = {
        'thread': thread,
        'posts': posts,
        'form': form,
    }
    return render(request, 'thread_detail.html', context)

@login_required
def thread_create(request):
    """Create a new thread and first post optionally."""
    if request.method == 'POST':
        tform = ThreadForm(request.POST)
        pform = PostForm(request.POST)  # optional first post
        if tform.is_valid() and pform.is_valid():
            thread = tform.save(commit=False)
            thread.user = request.user
            thread.save()

            # create initial post
            post = pform.save(commit=False)
            post.thread = thread
            post.user = request.user
            post.save()

            messages.success(request, "Thread created.")
            return redirect('thread_detail', thread_id=thread.id)
    else:
        tform = ThreadForm()
        pform = PostForm()

    return render(request, 'thread_form.html', {
        'form': tform,
        'post_form': pform,
        'creating': True,
    })

@login_required
def thread_edit(request, thread_id):
    """Edit a thread. Only the thread author may edit (adjust permission as needed)."""
    thread = get_object_or_404(Thread, id=thread_id)

    if request.user != thread.user and not request.user.has_perm('forum.change_thread'):
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

    return render(request, 'thread_form.html', {
        'form': form,
        'creating': False,
        'thread': thread,
    })

def user_profile(request, user_id):
    """
    Simple user profile view showing their recent threads and posts.
    Adjust imported User model if you use a custom user model.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_obj = get_object_or_404(User, id=user_id)

    recent_threads = Thread.objects.filter(user=user_obj).order_by('-created_at')[:20]
    recent_posts = Post.objects.filter(user=user_obj).select_related('thread').order_by('-created_at')[:20]

    return render(request, 'user_profile.html', {
        'profile_user': user_obj,
        'recent_threads': recent_threads,
        'recent_posts': recent_posts,
    })
