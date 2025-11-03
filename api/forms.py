from django import forms

# chatgpt form for sending request to ebay API
class EbaySearchForm(forms.Form):
    search_term = forms.CharField(
        label="Search Term",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Enter generic search term', 'class': 'form-control'})
    )
    item_count = forms.IntegerField(
        label="Number of Results",
        min_value=1,
        max_value=100,
        initial=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )