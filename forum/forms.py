from django import forms
from .models import Post, Thread

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
    class Meta:
        model = Thread
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter thread title'}),
            'content': text_area_widget(),
        }

    def clean_content(self) :
        return general_clean_content(self)
