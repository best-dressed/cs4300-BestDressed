"""Forms for interacting with the eBay API."""

from django import forms


class EbaySearchForm(forms.Form):
    """Form used to send search requests to the eBay API."""

    search_term = forms.CharField(
        label="Search Term",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter generic search term",
                "class": "form-control",
            }
        ),
    )

    item_count = forms.IntegerField(
        label="Number of Results",
        min_value=1,
        max_value=100,
        initial=3,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
            }
        ),
    )
