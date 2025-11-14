"""
Django views for the Best Dressed application.
"""

from django.shortcuts import render, get_object_or_404, redirect
from .models import Item, UserProfile, WardrobeItem, Outfit
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# IntegrityError: exception raised when database constraints are violated
from django.db import IntegrityError
from .forms import UserProfileForm, WardrobeItemForm, ItemForm, OutfitForm
from .recommendation import generate_recommendations
from django.http import JsonResponse
import threading

def index(request):
    """
    Landing page.
    If logged in → redirect straight to dashboard.
    If not logged in → show marketing homepage.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
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

    # check where user came from
    came_from = request.GET.get('from', None)
    
    # related items list, exclude the item we are primarily viewing
    items = Item.objects.exclude(pk=pk)

    context = {
        "item": item,
        "items": items,
        "already_saved": already_saved,
        "came_from": came_from,
    }
    return render(request, "item_detail.html", context)

# view for adding an item manually
# per chatGPT
def add_item(request):
    context = {}

    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            newItem = form.save()  # this writes the model instance to the database
            return redirect('add_item_success', pk=newItem.pk)
    else:
        form = ItemForm()  # empty form for GET request

    context['form'] = form
    return render(request, "add_item.html", context)

def add_item_success(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return render(request, "add_item_success.html", {'item':item})

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
    Display user's wardrobe items with filtering, search, and sorting options
    """
    user = request.user
    
    # Get filter, search, and sort parameters from URL
    category_filter = request.GET.get('category', None)
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort', '-created_at')  # default: newest first
    
    # Start with all user's wardrobe items
    wardrobe_items = WardrobeItem.objects.filter(user=user)
    
    # Apply search filter if provided
    if search_query:
        from django.db.models import Q
        wardrobe_items = wardrobe_items.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(color__icontains=search_query)
        )
    
    # Apply category filter if specified
    if category_filter and category_filter != 'all':
        wardrobe_items = wardrobe_items.filter(category=category_filter)
    
    # Apply sorting
    # order_by() sorts the database results
    # The '-' prefix means descending order (reverse)
    wardrobe_items = wardrobe_items.order_by(sort_by)
    
    # Get all available categories for the filter buttons
    categories = WardrobeItem.CATEGORY_CHOICES
    
    # Count items in each category (for display)
    category_counts = {}
    for category_value, category_label in categories:
        count = WardrobeItem.objects.filter(user=user, category=category_value).count()
        category_counts[category_value] = count
    
    # Define available sorting options (value, display_name)
    sort_options = [
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
        ('title', 'A-Z'),
        ('-title', 'Z-A'),
        ('brand', 'Brand (A-Z)'),
        ('-brand', 'Brand (Z-A)'),
    ]
    
    context = {
        'wardrobe_items': wardrobe_items,
        'categories': categories,
        'category_counts': category_counts,
        'current_filter': category_filter or 'all',
        'search_query': search_query,
        'current_sort': sort_by,
        'sort_options': sort_options,
    }
    
    return render(request, 'my_wardrobe.html', context)

@login_required
def delete_wardrobe_item(request, item_pk):
    """
    Delete an item from the user's wardrobe.
    
    Security: Only the owner can delete their items.
    """
    # Get the wardrobe item, but only if it belongs to the current user
    # also prevents users from deleting other users wardrobe items
    wardrobe_item = get_object_or_404(WardrobeItem, pk=item_pk, user=request.user)
    
    # Only allow POST requests (security best practice)
    if request.method == 'POST':
        item_title = wardrobe_item.title  # Save title for the message
        wardrobe_item.delete()
        
        messages.success(request, f'"{item_title}" has been removed from your wardrobe.')
        return redirect('my_wardrobe')
    
    # If GET request, show confirmation page (we'll create this template)
    context = {
        'item': wardrobe_item,
    }
    return render(request, 'confirm_delete_wardrobe_item.html', context)

@login_required
def add_wardrobe_item(request):
    """
    Add a new item to wardrobe manually (not from catalog).
    """
    if request.method == 'POST':
        form = WardrobeItemForm(request.POST)
        
        if form.is_valid():
            # create the wardrobe item (object) but don't save to DB yet
            wardrobe_item = form.save(commit=False)
            
            # set the user (security - only current user)
            wardrobe_item.user = request.user
            
            # catalog_item stays None (this is a manual upload)
            
            # now save to database
            wardrobe_item.save()
            
            messages.success(request, f'"{wardrobe_item.title}" has been added to your wardrobe!')
            return redirect('my_wardrobe')
    else:
        form = WardrobeItemForm()
    
    context = {
        'form': form,
        # For template to know this is "add" not "edit"
        'mode': 'add',
    }
    return render(request, 'wardrobe_item_form.html', context)

@login_required
def edit_wardrobe_item(request, item_pk):
    """
    Edit an existing wardrobe item.
    
    Important: This edits the WardrobeItem, NOT the catalog Item.
    Changes here only affect the user's personal wardrobe copy.
    """
    # Get the wardrobe item, ensuring it belongs to the current user
    wardrobe_item = get_object_or_404(WardrobeItem, pk=item_pk, user=request.user)
    
    if request.method == 'POST':
        # Pass the existing instance to the form
        form = WardrobeItemForm(request.POST, instance=wardrobe_item)
        
        if form.is_valid():
            # Save changes to the wardrobe item
            # Note: This does NOT affect catalog_item
            form.save()
            
            messages.success(request, f'"{wardrobe_item.title}" has been updated!')
            return redirect('my_wardrobe')
    else:
        # Pre-fill form with existing data
        form = WardrobeItemForm(instance=wardrobe_item)
    
    context = {
        'form': form,
        'mode': 'edit',  # Tell template this is edit mode
        'item': wardrobe_item,
    }
    return render(request, 'wardrobe_item_form.html', context)

@login_required
def recommendations(request):
    """
    View to display the recommendations page.
    The page shows a prompt input form where users can specify
    what kind of recommendations they want before generating them.
    """
    context = {}
    return render(request, 'recommendations.html', context)

@login_required
def generate_recommendations_ajax(request):
    """
    AJAX endpoint to generate AI-based clothing recommendations.
    
    Process:
    1. Get user's custom prompt from POST request
    2. Fetch user profile and available items
    3. Generate AI recommendations using the custom prompt
    4. Return JSON response with recommendations
    """
    user = request.user
    
    # Only accept POST requests with a user prompt
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method. Use POST.'
        }, status=405)
    
    try:
        # Get the user's custom prompt from the request
        import json
        data = json.loads(request.body)
        user_prompt = data.get('prompt', '').strip()
        
        if not user_prompt:
            return JsonResponse({
                'success': False,
                'error': 'Please provide a prompt describing what you\'re looking for.'
            }, status=400)
        
        # Get user profile and available items
        available_items = Item.objects.all()
        user_profile = UserProfile.objects.get(user=user)
        
        # Generate AI recommendations with the user's custom prompt
        ai_recommendations = generate_recommendations(available_items, user_profile, user_prompt)
        
        return JsonResponse({
            'success': True,
            'recommendations': ai_recommendations
        })
    
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User profile not found. Please complete your profile first.'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request data.'
        }, status=400)
    
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Unable to generate recommendations at this time. Please try again later.'
        }, status=500)

@login_required
def create_outfit(request):
    """
    Create a new outfit by selecting wardrobe items.
    
    GET: Display form with user's wardrobe items as checkboxes
    POST: Save the outfit with selected items
    """
    user = request.user
    
    if request.method == 'POST':
        # User submitted the form
        form = OutfitForm(user, request.POST)
        
        if form.is_valid():
            # Create outfit but don't save to database yet
            outfit = form.save(commit=False)
            
            # Set the user (security - only current user can create for themselves)
            outfit.user = user
            
            # Now save to database (this saves the outfit, but not the many-to-many items yet)
            outfit.save()
            
            # Save the many-to-many relationships (the items)
            # form.save_m2m() handles the many-to-many field (items)
            form.save_m2m()
            
            messages.success(request, f'Outfit "{outfit.name}" created successfully!')
            return redirect('my_outfits')
    else:
        # User is viewing the form (GET request)
        form = OutfitForm(user)
    
    # Get user's wardrobe items to display with images
    wardrobe_items = WardrobeItem.objects.filter(user=user)
    
    context = {
        'form': form,
        'wardrobe_items': wardrobe_items,
        'mode': 'create',  # Tell template this is create mode (not edit)
    }
    
    return render(request, 'create_outfit.html', context)

@login_required
def my_outfits(request):
    """
    Display all outfits created by the user.
    (Full implementation coming in Phase 6C)
    """
    user = request.user
    outfits = Outfit.objects.filter(user=user)
    
    context = {
        'outfits': outfits,
    }
    
    return render(request, 'my_outfits.html', context)