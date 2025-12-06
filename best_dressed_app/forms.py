"""Forms for various models in the app"""
from django import forms
from .models import UserProfile, WardrobeItem, Item, Outfit


class UserProfileForm(forms.ModelForm):
    """
    form for editing user profile information
    
    this is a ModelForm - Django automatically creates form fields
    based on the UserProfile model fields we specify in Meta
    """
    
    class Meta:
        """
        provides configuration for the ModelForm
        """
        # which model this form is for
        model = UserProfile
        
        # which fields from the model to include in the form
        fields = ['bio', 'style_preferences', 'favorite_colors']
        
        # customize how fields appear in the HTML
        widgets = {
            
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about your style...'
            }),
            # ^^^ this is the same as:
            # <textarea class="form-control" rows="4" placeholder="Tell us about your style..."></textarea>
            'style_preferences': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., casual, streetwear, minimalist'
            }),
            'favorite_colors': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., black, navy, olive green'
            }),
        }
        
        # custom labels for the fields
        labels = {
            'bio': 'About Your Style',
            'style_preferences': 'Style Preferences',
            'favorite_colors': 'Favorite Colors',
        }
        
        # help text that appears below each field
        help_texts = {
            'bio': 'Share your personal style story (optional)',
            'style_preferences': 'What styles do you gravitate towards?',
            'favorite_colors': 'Which colors do you wear most often?',
        }


class WardrobeItemForm(forms.ModelForm):
    """
    Form for creating and editing wardrobe items.
    
    Users can manually add items or edit existing ones.
    This form does NOT include the user or catalog_item fields
    as those are handled automatically.
    """
    
    class Meta:
        model = WardrobeItem
        fields = ['title', 'description', 'category', 'image_url', 'color', 'brand', 'season']
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Blue Denim Jacket'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the item...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/image.jpg'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Navy Blue'
            }),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Nike, Zara, H&M'
            }),
            'season': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., summer, winter, all-season'
            }),
        }
        
        labels = {
            'title': 'Item Name',
            'description': 'Description',
            'category': 'Category',
            'image_url': 'Image URL',
            'color': 'Color',
            'brand': 'Brand',
            'season': 'Season',
        }
        
        help_texts = {
            'image_url': 'Paste a link to an image of this item',
            'season': 'When do you typically wear this?',
        }


# mostly chatGPT here with some edits
class ItemForm(forms.ModelForm):
    """
    Form for creating or editing an Item instance.

    Uses Django's ModelForm to automatically generate form fields
    from the Item model. The form includes custom widgets for better
    styling and user guidance.

    Fields included:
    - title: Text input with placeholder.
    - description: Textarea with placeholder and 3 rows.
    - image_url: URL input with placeholder.
    - tag: Dropdown select.

    Comments:
    - The short description is not manually entered, hence excluded.
    """

    class Meta:
        model = Item
        # we don't get the short description manually
        fields = ['title', 'description', 'image_url', 'tag']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter image URL'}),
            'tag': forms.Select(attrs={'class': 'form-control'}),
        }


class OutfitForm(forms.ModelForm):
    """
    Form for creating and editing outfits.
    
    Users can name their outfit, describe it, and select wardrobe items.
    The items field uses checkboxes for multiple selection.
    """
    
    class Meta:
        model = Outfit
        fields = ['name', 'description', 'occasion', 'season', 'is_favorite', 'items']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Summer Date Night, Office Monday',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe this outfit and when to wear it...',
            }),
            'occasion': forms.Select(attrs={
                'class': 'form-select',
            }),
            'season': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_favorite': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            # CheckboxSelectMultiple creates a checkbox for each wardrobe item
            'items': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input',
            }),
        }
        
        labels = {
            'name': 'Outfit Name',
            'description': 'Description',
            'occasion': 'Occasion',
            'season': 'Season',
            'is_favorite': 'Mark as Favorite',
            'items': 'Select Items for This Outfit',
        }
        
        help_texts = {
            'name': 'Give your outfit a memorable name',
            'description': 'Optional - describe the look or when you\'d wear it',
            'items': 'Check all items you want to include in this outfit',
        }
    
    def __init__(self, user, *args, **kwargs):
        """
        Custom initialization to filter items by user.
        
        This ensures users only see their own wardrobe items, not other users' items.
        The __init__ method is called when the form is created.
        """
        super().__init__(*args, **kwargs)
        
        # Filter the items queryset to only show this user's wardrobe items
        # The 'items' field will only display wardrobe items belonging to this user
        self.fields['items'].queryset = WardrobeItem.objects.filter(user=user)
