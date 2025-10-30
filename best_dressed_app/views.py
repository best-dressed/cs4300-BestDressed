"""
Django views for the Best Dressed application.
"""

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Item
from django.contrib.auth.decorators import login_required
from .models import Item, UserProfile
from django.shortcuts import render
from .recommendation import generate_recommendations
from django.http import JsonResponse
import threading

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

@login_required
def dashboard(request):
    """
    User dashboard - central hub for accessing all user features
    """
    user = request.user
    
    # get or create user profile, retrieves database record; if it doesnt exist, create it
    # profile: UserProfile object
    # created: boolean for if object was just created (True) or if it already exists (False)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # python dictionary that passes data from Python (Django view) to the HTML template
    context = {
        'wardrobe_count': 1,
        'outfit_count': 2,
        'recommendation_count': 3,
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def recommendations(request):
    """
    View to display the recommendations page.
    The page loads immediately with a loading indicator,
    then JavaScript fetches the actual recommendations via AJAX.
    """
    context = {
        'loading': True,
    }
    return render(request, 'recommendations.html', context)

@login_required
def generate_recommendations_ajax(request):
    """
    AJAX endpoint to generate AI-based clothing recommendations.
    
    Process:
    1. Fetch user profile and available items
    2. Generate AI recommendations
    3. Return JSON response with recommendations
    """
    user = request.user
    
    try:
        # Get user profile and available items
        available_items = Item.objects.all()
        user_profile = UserProfile.objects.get(user=user)
        
        # Generate AI recommendations
        ai_recommendations = generate_recommendations(available_items, user_profile)
        
        return JsonResponse({
            'success': True,
            'recommendations': ai_recommendations
        })
    
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User profile not found. Please complete your profile first.'
        }, status=404)
    
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Unable to generate recommendations at this time. Please try again later.'
        }, status=500)
