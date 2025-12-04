from django import forms
from .models import Post, Thread
from best_dressed_app.models import Outfit

def general_clean_content(self):
    content = self.cleaned_data.get("content", "").strip()
    if not content:
        raise forms.ValidationError("Post content cannot be empty.")
    max_len = 2000
    if len(content) > max_len:
        raise forms.ValidationError(f"Post cannot be longer than {max_len} characters.")
    return content

def text_area_widget() :
    return forms.Textarea(attrs={
            "rows": 6,
            "placeholder": "Write post...",
            "class": "form-control",
        })

class PostForm(forms.ModelForm):
    content = forms.CharField(
        label="Content",
        widget=text_area_widget(),
        required=True,
    )

    def clean_content(self) :
        return general_clean_content(self)

    class Meta:
        model = Post
        fields = ('content',)



class ThreadForm(forms.ModelForm):
  
    #NEWNEWNEW
    attached_outfit = forms.ModelChoiceField(
        queryset=Outfit.objects.none(), 
        required=False,
        empty_label="None (no outfit attached)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Attach an Outfit (Optional)"
    )
    #NEWNEWNEW
   
    class Meta:
        model = Thread
        fields = ['title', 'content', 'attached_outfit']  # ADD 'attached_outfit' HERE
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter thread title'}),
            'content': text_area_widget(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract user from kwargs
        super().__init__(*args, **kwargs)
        
        # Only show the current user's outfits
        if user:
            self.fields['attached_outfit'].queryset = Outfit.objects.filter(user=user).order_by('-created_at')

    def clean_content(self):
        return general_clean_content(self)