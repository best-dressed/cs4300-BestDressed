"""
Django views for the Best Dressed application.
"""

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Item
from django.contrib.auth.decorators import login_required

def index(request):
    """
    View for the index page, as of now this is a landing page.
    """
    if (request.user.is_authenticated) :
        return render(request, '../templates/index_signed_in.html')
       
    else :
        return render(request, '../templates/index.html')

"""@login_required(login_url='login')   # <- forces login first
def index_signed_in(request):
    return render(request, 'index_signed_in.html')"""

def login(request):
    """
    View the login page
    """
    return render(request, 'login.html')

def signup(request):
    """
    View the signup page
    """
    return render(request, 'signup.html')

def item_listing(request):
    items = Item.objects.all()
    return render(request, "item_listing.html", {'items': items})

# for a particular item view
def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    # related items list, exclude the item we are primarily viewing
    items = Item.objects.exclude(pk=pk)

    context = {
        "item": item,
        "items": items

    }
    return render(request, "item_detail.html", context)

