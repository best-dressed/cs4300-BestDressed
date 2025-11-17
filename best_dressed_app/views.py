"""
Django views for the Best Dressed application.
"""

from django.shortcuts import render, get_object_or_404, redirect
from .models import Item, UserProfile, WardrobeItem, Outfit, SavedRecommendation, HiddenItem
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

# primary item listing view for main page
def item_listing(request):
    query = request.GET.get("q")
    if query:
        from django.db.models import Q
        items = Item.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
    else:
        items = Item.objects.all()

    # Filter out items hidden by current user
    if request.user.is_authenticated:
        hidden_ids = request.user.hidden_items.values_list("item__id", flat=True)
        items = items.exclude(pk__in=hidden_ids)

    return render(request, "item_listing.html", {'items': items, 'query': query})

# handle ajax post from item_card.html when the user hides items from item listing w the little icon
@login_required
def ajax_hide_item(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    item_id = request.POST.get("item_id")
    if not item_id:
        return JsonResponse({"error": "Missing item_id"}, status=400)

    item = get_object_or_404(Item, pk=item_id)

    # Create or get
    obj, created = HiddenItem.objects.get_or_create(
        user=request.user,
        item=item
    )

    return JsonResponse({"success": True, "hidden": created})
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

    # block hidden items here too
    if request.user.is_authenticated:
        hidden_ids = request.user.hidden_items.values_list("item__id", flat=True)
        items = items.exclude(pk__in=hidden_ids)

    context = {
        "item": item,
        "items": items,
        "already_saved": already_saved,
        "came_from": came_from,
    }
    return render(request, "item_detail.html", context)

# view for adding an item manually
# per chatGPT
@login_required
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
    Enhanced user dashboard - central hub with statistics and quick actions.
    
    Displays:
    - Wardrobe and outfit counts
    - Outfit statistics (by season, occasion, favorites)
    - Recent outfits
    - Random outfit suggestion
    """
    user = request.user
    
    # get or create user profile, retrieves database record; if it doesnt exist, create it
    # profile: UserProfile object
    # created: boolean for if object was just created (True) or if it already exists (False)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # get actual counts (of number of items in Wardrobe and number of Outfits) from the database for the logged in user
    wardrobe_count = WardrobeItem.objects.filter(user=user).count()
    outfit_count = Outfit.objects.filter(user=user).count()
    # implement later
    recommendation_count = 0  
    
    # Outfit statistics by category
    favorites_count = Outfit.objects.filter(user=user, is_favorite=True).count()
    
    # Count outfits by season
    # values('season') groups the results by season
    # annotate(count=Count('id')) counts how many in each group
    season_stats = Outfit.objects.filter(user=user).values('season').annotate(count=Count('id'))
    
    # Count outfits by occasion
    occasion_stats = Outfit.objects.filter(user=user).values('occasion').annotate(count=Count('id'))
    
    # Recent outfits (last 4)
    # prefetch_related loads all items for these outfits efficiently
    recent_outfits = Outfit.objects.filter(user=user).prefetch_related('items').order_by('-created_at')[:4]
    
    # Random outfit suggestion ("Outfit of the Day")
    # order_by('?') randomizes the order, [:1] gets just one
    random_outfit = Outfit.objects.filter(user=user).order_by('?').first()

    # python dictionary that passes data from Python (Django view) to the HTML template   
    context = {
        'wardrobe_count': wardrobe_count,
        'outfit_count': outfit_count,
        'recommendation_count': recommendation_count,
        'favorites_count': favorites_count,
        'season_stats': season_stats,
        'occasion_stats': occasion_stats,
        'recent_outfits': recent_outfits,
        'random_outfit': random_outfit,
    }
    
    return render(request, 'dashboard.html', context)


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
    outfit_count = Outfit.objects.filter(user=user).count()
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
    catalog_item = get_object_or_404(Item, pk=item_pk)

    # Only allow POST requests (security best practice)
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('item_detail', pk=item_pk)

    # Try to create the item, catch if it already exists
    try:
        WardrobeItem.objects.create(
            user=request.user,
            title=catalog_item.title,
            description=catalog_item.description,
            image_url=catalog_item.image_url,
            category='other',
            catalog_item=catalog_item
        )
        success_message = 'Item added to wardrobe!'
        status = 'added'

    except IntegrityError:
        # Item already exists in wardrobe
        success_message = 'Already in wardrobe'
        status = 'exists'

    # AJAX response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': success_message,
            'status': status
        })

    # Normal redirect
    if status == 'exists':
        messages.info(request, f'"{catalog_item.title}" is already in your wardrobe.')
    else:
        messages.success(request, f'"{catalog_item.title}" has been added to your wardrobe!')

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
    Also displays past AI recommendations with their prompts.
    """
    user = request.user
    
    # Fetch past recommendations for this user (newest first)
    past_recommendations = SavedRecommendation.objects.filter(user=user).prefetch_related('recommended_items')
    
    context = {
        'past_recommendations': past_recommendations,
    }
    return render(request, 'recommendations.html', context)

@login_required
def generate_recommendations_ajax(request):
    """
    AJAX endpoint to generate AI-based clothing recommendations.
    
    Process:
    1. Get user's custom prompt from POST request
    2. Fetch user profile and available items
    3. Generate AI recommendations using the custom prompt
    4. Parse recommended item IDs from AI response
    5. Return JSON response with recommendations and item details
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
        import re
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
        
        # Parse the recommended item IDs from the AI response
        # Look for pattern: RECOMMENDED_ITEMS: [id1, id2, id3, ...]
        recommended_item_ids = []
        match = re.search(r'RECOMMENDED_ITEMS:\s*\[([\d,\s]+)\]', ai_recommendations)
        if match:
            # Extract the IDs and convert to integers
            ids_str = match.group(1)
            recommended_item_ids = [int(id.strip()) for id in ids_str.split(',') if id.strip().isdigit()]
            
            # Remove the RECOMMENDED_ITEMS line from the text
            ai_recommendations = re.sub(r'\n*RECOMMENDED_ITEMS:\s*\[[\d,\s]+\]\n*', '', ai_recommendations).strip()
        
        # Fetch the actual Item objects
        recommended_items = []
        item_objects = []
        if recommended_item_ids:
            items = Item.objects.filter(id__in=recommended_item_ids)
            # Create a dictionary to maintain order
            items_dict = {item.id: item for item in items}
            
            # Build the list in the order specified by the AI
            for item_id in recommended_item_ids:
                if item_id in items_dict:
                    item = items_dict[item_id]
                    item_objects.append(item)
                    recommended_items.append({
                        'id': item.id,
                        'title': item.title,
                        'description': item.description,
                        'short_description': item.short_description,
                        'image_url': item.image_url,
                        'tag': item.tag,
                        'detail_url': item.get_absolute_url(),
                    })
        
        # Save the recommendation to the database
        saved_rec = SavedRecommendation.objects.create(
            user=user,
            prompt=user_prompt,
            ai_response=ai_recommendations
        )
        
        # Associate the recommended items with the saved recommendation
        if item_objects:
            saved_rec.recommended_items.set(item_objects)
        
        return JsonResponse({
            'success': True,
            'recommendations': ai_recommendations,
            'items': recommended_items
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
    Display all outfits created by the user with filtering options.
    """
    user = request.user
    
    # Get filter parameters from URL
    occasion_filter = request.GET.get('occasion', None)
    season_filter = request.GET.get('season', None)
    favorites_only = request.GET.get('favorites', None)
    
    # Start with all user's outfits
    outfits = Outfit.objects.filter(user=user)
    
    # Apply occasion filter if specified
    if occasion_filter and occasion_filter != 'all':
        outfits = outfits.filter(occasion=occasion_filter)
    
    # Apply season filter if specified
    if season_filter and season_filter != 'all':
        outfits = outfits.filter(season=season_filter)
    
    # Apply favorites filter if specified
    if favorites_only == 'true':
        outfits = outfits.filter(is_favorite=True)
    
    # Prefetch related items for efficiency
    # This loads all items for all outfits in one database query
    # instead of making a separate query for each outfit (N+1 problem)
    outfits = outfits.prefetch_related('items')
    
    # Get available filter options from the model choices
    occasion_choices = Outfit._meta.get_field('occasion').choices
    season_choices = Outfit._meta.get_field('season').choices
    
    context = {
        'outfits': outfits,
        'occasion_filter': occasion_filter or 'all',
        'season_filter': season_filter or 'all',
        'favorites_only': favorites_only == 'true',
        'occasion_choices': occasion_choices,
        'season_choices': season_choices,
    }
    
    return render(request, 'my_outfits.html', context)

@login_required
def outfit_detail(request, outfit_pk):
    """
    View detailed information about a specific outfit.
    """
    outfit = get_object_or_404(Outfit, pk=outfit_pk, user=request.user)
    
    context = {
        'outfit': outfit,
    }
    
    return render(request, 'outfit_detail.html', context)

@login_required
def edit_outfit(request, outfit_pk):
    """
    Edit an existing outfit.
    """
    outfit = get_object_or_404(Outfit, pk=outfit_pk, user=request.user)
    
    # Redirect to create page for now
    messages.info(request, 'Edit functionality coming soon!')
    return redirect('my_outfits')

@login_required
def delete_outfit(request, outfit_pk):
    """
    Delete an outfit with confirmation.
    
    GET: Show confirmation page
    POST: Actually delete the outfit
    
    Security: Only the owner can delete their outfits
    """
    # Get the outfit, ensuring it belongs to current user (security)
    outfit = get_object_or_404(Outfit, pk=outfit_pk, user=request.user)
    
    if request.method == 'POST':
        # User confirmed deletion
        outfit_name = outfit.name  # Save name for success message
        outfit.delete()  # Delete from database
        
        messages.success(request, f'Outfit "{outfit_name}" has been deleted.')
        return redirect('my_outfits')
    
    # GET request: show confirmation page
    context = {
        'outfit': outfit,
    }
    return render(request, 'confirm_delete_outfit.html', context)

@login_required
def edit_outfit(request, outfit_pk):
    """
    Edit an existing outfit.
    
    Allows user to:
    - Change name, description, occasion, season, favorite status
    - Add or remove items from the outfit
    
    GET: Display pre-filled form
    POST: Save changes
    """
    # Get the outfit, ensuring it belongs to current user (security)
    outfit = get_object_or_404(Outfit, pk=outfit_pk, user=request.user)
    
    if request.method == 'POST':
        # User submitted the form with changes
        # instance=outfit tells the form to update the existing outfit, not create a new one
        form = OutfitForm(request.user, request.POST, instance=outfit)
        
        if form.is_valid():
            # Save changes to the outfit
            # commit=False means "create the object but don't save to DB yet"
            outfit = form.save(commit=False)
            outfit.user = request.user  # Ensure user doesn't change (security)
            outfit.save()
            
            # Save the many-to-many relationships (the items)
            # This must happen after the outfit is saved
            form.save_m2m()
            
            messages.success(request, f'Outfit "{outfit.name}" has been updated!')
            return redirect('outfit_detail', outfit_pk=outfit.pk)
    else:
        # GET request: show form pre-filled with current outfit data
        # instance=outfit pre-fills the form with existing values
        form = OutfitForm(request.user, instance=outfit)
    
    # Get user's wardrobe items to display with images
    wardrobe_items = WardrobeItem.objects.filter(user=request.user)
    
    context = {
        'form': form,
        'wardrobe_items': wardrobe_items,
        'outfit': outfit,
        'mode': 'edit',  # Tell template this is edit mode (not create)
    }
    
    return render(request, 'edit_outfit.html', context)
