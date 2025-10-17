"""
Django views for the Best Dressed application.
"""

from django.shortcuts import render

def index(request):
    """
    View for the index page, as of now this is a landing page.
    """
    return render(request, '../templates/index.html')

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

