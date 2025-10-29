"""
Django views for the Best Dressed application.
"""

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Item
from django.contrib.auth.decorators import login_required
from .models import Item, UserProfile
from django.shortcuts import render
from .forms import UserProfileForm

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
def account_settings(request):
    """
    View and edit account settings.
    
    This view handles both displaying the form (GET request)
    and processing form submissions (POST request).
    """
    user = request.user
    
    # get or create user profile, retrieves database record; if it doesnt exist, create it
    # profile: UserProfile object
    # created: boolean for if object was just created (True) or if it already exists (False)    
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # check if this is a form submission (POST) or just viewing the page (GET)
    if request.method == 'POST':
        # user submitted the form - process it
        form = UserProfileForm(request.POST, instance=profile)
        
        # validate the form data
        if form.is_valid():
            # save the changes to the database
            form.save()
            
            # add a success message (display in template)
            from django.contrib import messages
            messages.success(request, 'Your profile has been updated successfully!')
            
            # redirect back to account settings (prevents duplicate submissions)
            from django.shortcuts import redirect
            return redirect('account_settings')
    else:
        # user is just viewing the page - show form with current data
        form = UserProfileForm(instance=profile)
    
    # python dictionary that passes data from Python (Django view) to the HTML template
    context = {
        'profile': profile,
        # pass the form to the template
        'form': form,
    }
    
    return render(request, 'account_settings.html', context)
