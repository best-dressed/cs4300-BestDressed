"""
Views for moderation stuff
(mainly just error pages)
"""
from django.shortcuts import render
from .moderation_common import get_client_ip
from .models import BannedIP

def filtered_content_message(request):
    """ view for page when your content was filtered """
    return render(
        request,
        "errors/filtered_content.html"
    )

def ip_ban_page(request):
    """ View for page when IP was banned """
    user_ip = get_client_ip(request)
    bans = BannedIP.objects.filter(ip_address=user_ip)

    # Get the first active ban (if any)
    active_ban = next((ban for ban in bans if ban.is_active()), None)

    return render(
        request,
        "errors/ip_ban.html",
        {"ban_reason": active_ban.reason if active_ban else None}
    )

def invalid_post(request):
    """
    Display an error page when a post is invalid.
    """
    return render(request, "errors/invalid_post.html")
