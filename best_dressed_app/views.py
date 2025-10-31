"""
Django views for the Best Dressed application.
"""

from django.shortcuts import render, get_object_or_404, redirect
from .models import Item, UserProfile, WardrobeItem
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# IntegrityError: exception raised when database constraints are violated
from django.db import IntegrityError
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

# # for a particular item view
# def item_detail(request, pk):
#     item = get_object_or_404(Item, pk=pk)
#     # related items list, exclude the item we are primarily viewing
#     items = Item.objects.exclude(pk=pk)

#     context = {
#         "item": item,
#         "items": items

#     }
#     return render(request, "item_detail.html", context)

# for a particular item view
def item_detail(request, pk):
    # get/fetch the item (if it exists)
    item = get_object_or_404(Item, pk=pk)
    
    # check if user has already saved this item
    already_saved = False
    if request.user.is_authenticated:
        already_saved = WardrobeItem.objects.filter(
            # get current (logged in) user
            user=request.user,
            catalog_item=item
        ).exists()
    
    # related items list, exclude the item we are primarily viewing
    items = Item.objects.exclude(pk=pk)

    context = {
        "item": item,
        "items": items,
        "already_saved": already_saved,
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
    
    # get actual counts (of number of items in Wardrobe) from the database for the logged in user
    wardrobe_count = WardrobeItem.objects.filter(user=user).count()
    # implement this later when we build Outfits
    outfit_count = 0  
    # implement this later with AI recommendations
    recommendation_count = 0  

    # python dictionary that passes data from Python (Django view) to the HTML template
    context = {
        'wardrobe_count': wardrobe_count,
        'outfit_count': outfit_count,
        'recommendation_count': recommendation_count,
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

@login_required
def save_to_wardrobe(request, item_pk):
    """
    Save a catalog item (from the item listing page) to the user's wardrobe.
    
    This view handles POST requests to add items from the catalog
    to a user's personal wardrobe. It prevents duplicate saves
    and provides appropriate feedback messages.
    
    Args:
        request: The HTTP request object
        item_pk: Primary key of the Item to save
    """
    
    # Get the catalog item or return 404 if it doesn't exist
    # This is safer than Item.objects.get() which would raise an exception
    catalog_item = get_object_or_404(Item, pk=item_pk)
    
    # Only allow POST requests (security best practice)
    # Prevents accidental saves from just visiting a URL
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('item_detail', pk=item_pk)
    
    # using try/except:
    # - guarantees no dupes (or race conditions)
    # - allows for less code and fewer db queries
    try:
        # Try to create a new wardrobe item
        # If it already exists (violates unique_together), this will raise IntegrityError
        wardrobe_item = WardrobeItem.objects.create(
            user=request.user,
            title=catalog_item.title,
            description=catalog_item.description,
            image_url=catalog_item.image_url,
            category='other',  # Default category, user can change later
            catalog_item=catalog_item
        )
        
        # show a success message
        messages.success(
            request, 
            f'"{catalog_item.title}" has been added to your wardrobe!'
        )
        
    except IntegrityError:
        # Item already exists in wardrobe (unique_together constraint violated)
        # This is not really an error, just inform the user
        messages.info(
            request,
            f'"{catalog_item.title}" is already in your wardrobe.'
        )
    
    # Redirect back to the item detail page
    # Using redirect prevents form resubmission if user refreshes the page
    return redirect('item_detail', pk=item_pk)

@login_required
def my_wardrobe(request):
    """
    Display user's wardrobe items with filtering options
    """
    user = request.user
    
    # Get filter parameter from URL (e.g., ?category=top)
    category_filter = request.GET.get('category', None)
    
    # Start with all user's wardrobe items
    wardrobe_items = WardrobeItem.objects.filter(user=user)
    
    # Apply category filter if specified
    if category_filter and category_filter != 'all':
        wardrobe_items = wardrobe_items.filter(category=category_filter)
    
    # Get all available categories for the filter buttons
    # This creates a list of tuples: [('top', 'Top'), ('bottom', 'Bottom'), ...]
    categories = WardrobeItem.CATEGORY_CHOICES
    
    # Count items in each category (for display)
    category_counts = {}
    for category_value, category_label in categories:
        count = WardrobeItem.objects.filter(user=user, category=category_value).count()
        category_counts[category_value] = count
    
    context = {
        'wardrobe_items': wardrobe_items,
        'categories': categories,
        'category_counts': category_counts,
        'current_filter': category_filter or 'all',
    }
    
    return render(request, 'my_wardrobe.html', context)