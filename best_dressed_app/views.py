"""
Django views for the Best Dressed application.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def index(request):
    """
    View for the index page, as of now this is a landing page.
    """
    if (request.user.is_authenticated) :
        return render(request, '../templates/index_signed_in.html')
       
    else :
        return render(request, '../templates/index.html')

@login_required(login_url='login')   # <- forces login first
def index_signed_in(request):
    return render(request, 'index_signed_in.html')

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

