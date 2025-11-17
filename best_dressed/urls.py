"""
URL configuration for best_dressed project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from best_dressed_app import views



urlpatterns = [
    path('', views.index, name="index"),
     path('login/', views.login, name="login"),
     path('signup/', views.signup, name="signup"),
    path("accounts/", include("users.urls")),
    # ebay api path
    path('', include("api.urls")),
    path('admin/', admin.site.urls),

    # dashboard and user features
    path('dashboard/', views.dashboard, name="dashboard"),
    path('account/', views.account_settings, name="account_settings"),
    
    # wardrobe and wardrobe features
    path('wardrobe/', views.my_wardrobe, name="my_wardrobe"),
    path('wardrobe/add/', views.add_wardrobe_item, name="add_wardrobe_item"),
    path('wardrobe/edit/<int:item_pk>/', views.edit_wardrobe_item, name="edit_wardrobe_item"),
    path('wardrobe/delete/<int:item_pk>/', views.delete_wardrobe_item, name="delete_wardrobe_item"),


    # outfits and outfit features
    path('outfits/create/', views.create_outfit, name='create_outfit'),
    path('outfits/', views.my_outfits, name='my_outfits'),
    path('outfits/<int:outfit_pk>/', views.outfit_detail, name='outfit_detail'),
    path('outfits/<int:outfit_pk>/edit/', views.edit_outfit, name='edit_outfit'),
    path('outfits/<int:outfit_pk>/delete/', views.delete_outfit, name='delete_outfit'),
    path('outfits/<int:outfit_pk>/toggle-favorite/', views.toggle_outfit_favorite, name='toggle_outfit_favorite'),
    path('outfits/<int:outfit_pk>/duplicate/', views.duplicate_outfit, name='duplicate_outfit'),


    # item listing/catalog
    path('item_listing/', views.item_listing, name="item_listing"),
    path('item/<int:pk>/', views.item_detail, name="item_detail"),
    # pattern (item/<int:item_pk>/save/):
    # - item/: text
    # - <int:item_pk>: captures an integer from URL, passes it as `item_pk` parameter
    # - /save/: text
    # - views.save_to_wardrobe: view funtion to call
    # - name="save_to_wardrobe": name for reverse URL lookup
    path('item/<int:item_pk>/save/', views.save_to_wardrobe, name="save_to_wardrobe"),
    path('add_item/', views.add_item, name="add_item"),
    path('add_item/success/<int:pk>/', views.add_item_success, name="add_item_success"),

    # ai recommendations
    path('recommendations/', views.recommendations, name="recommendations"),
    path('recommendations/generate/', views.generate_recommendations_ajax, name="generate_recommendations_ajax"),

    # forums
    path("forum/", include("forum.urls")),
]
