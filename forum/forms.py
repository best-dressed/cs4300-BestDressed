from django import forms
from .models import Post, Thread

class PostForm(forms.ModelForm):
    content = forms.CharField(
        label="Content",
        widget=forms.Textarea(attrs={
            "rows": 6,
            "placeholder": "Write post...",
            "class": "form-control",
        }),
        required=True,
    )

    class Meta:
        model = Post
        fields = ("content",)

    def clean_content(self):
        content = self.cleaned_data.get("content", "").strip()
        if not content:
            raise forms.ValidationError("Post content cannot be empty.")
        # optional: enforce a maximum length (uncomment and set if desired)
        max_len = 2000
        if len(content) > max_len:
            raise forms.ValidationError(f"Post cannot be longer than {max_len} characters.")
        return content

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['title']