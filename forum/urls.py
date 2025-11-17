from django.urls import path
from . import views

urlpatterns = [
    path('', views.threads, name='threads'),
    path('threads/new/', views.thread_create, name='thread_create'),
    path('threads/<int:thread_id>/', views.thread_detail, name='thread_detail'),
    path('threads/<int:thread_id>/edit/', views.thread_edit, name='thread_edit'),
    path('threads/<int:thread_id>/delete/', views.thread_delete, name='thread_delete'), 
    # path('users/<int:user_id>/', views.user_profile, name='user_profile'),
    path('posts/<int:post_id>/delete/', views.post_delete, name='post_delete'),
    path('posts/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    path('thread/<int:thread_id>/like/', views.toggle_thread_like, name='toggle_thread_like'),
    path('post/<int:post_id>/like/', views.toggle_post_like, name='toggle_post_like'),
    path('thread/<int:thread_id>/save/', views.toggle_thread_save, name='toggle_thread_save'),
    path('saved/', views.my_saved_threads, name='my_saved_threads'),
]
