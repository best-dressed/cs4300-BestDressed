from django.urls import path
from . import views

urlpatterns = [
    path('threads/', views.threads, name='threads'),
    path('threads/new/', views.thread_create, name='thread_create'),
    path('threads/<int:thread_id>/', views.thread_detail, name='thread_detail'),
    path('threads/<int:thread_id>/edit/', views.thread_edit, name='thread_edit'),
    path('threads/<int:thread_id>/delete/', views.thread_delete, name='thread_delete'), 
    path('users/<int:user_id>/', views.user_profile, name='user_profile'),
]
