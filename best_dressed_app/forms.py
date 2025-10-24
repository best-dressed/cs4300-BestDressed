from django import forms
from .models import Item

# mostly chatGPT here with some edits
class ItemForm(forms.ModelForm):
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
