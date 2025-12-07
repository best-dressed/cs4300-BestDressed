"""Forms for the forum app."""
# pylint: disable=too-few-public-methods,no-member
from django import forms
from best_dressed_app.models import Outfit
from .models import Post, Thread


def general_clean_content(self):
    """Validate and clean content field."""
    content = self.cleaned_data.get("content", "").strip()
    if not content:
        raise forms.ValidationError("Post content cannot be empty.")
    max_len = 2000
    if len(content) > max_len:
        raise forms.ValidationError(f"Post cannot be longer than {max_len} characters.")
    return content


def text_area_widget():
    """Return a configured textarea widget."""
    return forms.Textarea(attrs={
        "rows": 6,
        "placeholder": "Write post...",
        "class": "form-control",
    })


class PostForm(forms.ModelForm):
    """Form for creating and editing posts."""
    content = forms.CharField(
        label="Content",
        widget=text_area_widget(),
        required=True,
    )

    def clean_content(self):
        """Validate post content."""
        return general_clean_content(self)

    class Meta:
        """Meta options for PostForm."""
        model = Post
        fields = ('content',)


class ThreadForm(forms.ModelForm):
    """Form for creating and editing threads with optional outfit attachment."""
    attached_outfit = forms.ModelChoiceField(
        queryset=Outfit.objects.none(),
        required=False,
        empty_label="None (no outfit attached)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Attach an Outfit (Optional)"
    )

    class Meta:
        """Meta options for ThreadForm."""
        model = Thread
        fields = ['title', 'content', 'attached_outfit']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter thread title'
            }),
            'content': text_area_widget(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['attached_outfit'].queryset = Outfit.objects.filter(
                user=user
            ).order_by('-created_at')

    def clean_content(self):
        """Validate thread content."""
        return general_clean_content(self)
