from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def filtered_content_message(request):
    return render(
        request,
        "filtered_content.html"
    )
