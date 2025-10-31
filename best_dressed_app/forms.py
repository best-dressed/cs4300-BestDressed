from django import forms
from .models import UserProfile, WardrobeItem


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