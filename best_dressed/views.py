"""
Django views for the Best Dressed application.
"""

from django.shortcuts import render

def index(request):
    """
    View for the index page, currently just a splash page. 
    """
    return render(request, 'index.html')

def itemListing(request):

    return render(request, "item-listing.html")