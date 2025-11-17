# This file contains some decorator functions that are useful for 
# bans and other stuff
import re
from django.http import HttpResponseRedirect
from django.urls import reverse

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
                    return HttpResponseRedirect(reverse(""))
            return func(request,*args,**kwargs)
        return wrapper
    return decorator

