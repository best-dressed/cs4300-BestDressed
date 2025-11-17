# This file contains some decorator functions that are useful for 
# bans and other stuff
import re
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import BannedIP

REDIRECT = 0
VALID = 1    

def get_content_filters() :
    filters = [] 
    try :
        # go through line by line and get a pattern from filters.txt
        with open("moderation/filters.txt") as f : 
            for pattern in f : 
                filters.append(re.compile(pattern.rstrip("\n")))
    except FileNotFoundError :
        print("Failed to open filters.txt, adding no filters instead")
        filters = [] 
    return filters


filters = get_content_filters()

def content_filter_decorator(*accessors,validator=(lambda value : True)) :
    """This is a decorator that is used when a user is posting
    
    It allows for arbitrarily many accessors to get the text to filter.
    Accessors should be functions that act on a request to find the text.

    Validator is something to ensure that the request has the right datafields. 
    Default is to simply assume the value is valid
    """
    def decorator(func) :
        def wrapper (request,*args, **kwargs):
            # If we have a post request, 
            if request.method == "POST" :
                # validate the request to see if it has the right data fields
                if validator(request) :
                # Get the values and filter them with the word filters.
                    for accessor in accessors :
                        for pattern in filters : 
                            print(accessor(request))
                            if pattern.match(accessor(request)) :
                                return HttpResponseRedirect(reverse("filtered_content"))
                else :
                    return HttpResponseRedirect(reverse("invalid_post"))
            return func(request,*args,**kwargs)
        return wrapper
    return decorator

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Can be a comma-separated list if multiple proxies are involved
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip

def not_ip_banned_generator(*, check=lambda request: True):
    """
    Blocks requests from banned IPs.

    By default it blocks all requests, but you can pass a custom
    `check` function (e.g. only block POSTs).
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            user_ip = get_client_ip(request)
            bans = BannedIP.objects.filter(ip_address=user_ip)

            # If the request is relevant and user has active bans
            if check(request) and any(ban.is_active() for ban in bans):
                # Redirect to your IP ban page
                return redirect("ip_ban")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

not_ip_banned = not_ip_banned_generator()
