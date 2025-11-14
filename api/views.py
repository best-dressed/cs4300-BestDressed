from django.shortcuts import render
from django.contrib import messages
import hashlib
import json
from django.http import (
    HttpResponse,
    JsonResponse,
    HttpResponseBadRequest
)
import os
import requests
import base64
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import logging
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature, InvalidKey
from best_dressed_app.models import Item
from .forms import *
from safetext import SafeText
# for a better interactive item adding
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

## Basically a giant amalgamation of
# https://stackoverflow.com/questions/68569773/ebay-marketplace-account-deletion-closure-notifications
# and a bunch of chatGPT code for processing json, and adapting signature validation to use cryptography lib

EBAY_VERIFICATION_TOKEN = os.environ.get('EBAY_VERIFICATION_TOKEN')
EBAY_BASE64_AUTHORIZATION_TOKEN = os.environ.get("EBAY_BASE64_AUTHORIZATION_TOKEN")
# need to have this to support accepting requests to delete data from Ebay users who delete accounts.
@csrf_exempt
def ebay_marketplace_deletion_notification(request):
    challengeCode = request.GET.get('challenge_code')
    X_EBAY_SIGNATURE = 'X-Ebay-Signature'


    # reply to challengecode basically just saying "yeah we got it"
    if challengeCode is not None:
        verificationToken = EBAY_VERIFICATION_TOKEN # random 32-80 char string
        endpoint_url = "https://best-dressed.net/auth/ebay_market_delete/"
        m = hashlib.sha256((challengeCode + verificationToken + endpoint_url).encode('utf-8'))
        return JsonResponse({"challengeResponse": m.hexdigest()}, status=200)

    # when ebay sends their delete request verify it with public key then delete
    elif request.method == 'POST':
        # the ebay signature is a json body encoded so once we decode we access its elements
        x_ebay_signature = request.headers["X-Ebay-Signature"]
        x_ebay_signature_decoded = json.loads(base64.b64decode(x_ebay_signature).decode('utf-8'))
        kid = x_ebay_signature_decoded['kid']
        signature = x_ebay_signature_decoded['signature']
        logger.warning(f"SIGNATURE: {signature}")
        logger.warning(f"kid: {kid}")

        # get public key for verification
        # DOES NOT WORK, Probably... needs to be tested on Prod with actual requests from ebay.
        # afaik impossible to do the ebay call for public key unless ebay themselves sent req.
        # https://developer.ebay.com/api-docs/commerce/notification/resources/public_key/methods/getPublicKey
        public_key = None
        try:

            oauth_access_token = get_oath_token()

            # send out a call to get public key
            ebay_verification_url = f'https://api.ebay.com/commerce/notification/v1/public_key/{kid}'
            pkRequest = requests.get(url=ebay_verification_url,
                                            headers = {
                                                'Authorization': f'Bearer {oauth_access_token}'
                                            },
                                            data = {})
            logger.warning(f"PKRESPONSE: {pkRequest.json()}")
            if pkRequest.status_code == 200:
                pkResponse = pkRequest.json()
                public_key = pkResponse['key']

        # catch errors
        except Exception as e:
            message_title = f"Ebay Marketplace Account Deletion: Error performing validation"
            logger.error(f"{message_title} Error: {e}")
            return JsonResponse({}, status=500)

        # if we get here we have the public key and everything from ebay,
        # so use it to verify signature actually came from eBay
        pk = public_key
        msg_body_bytes = request.body
        public_key_pem = pk.encode("utf-8")

        # figure this out later
        try:
            pk = serialization.load_pem_public_key(public_key_pem)
        except (ValueError, InvalidKey):
            logging.error("Invalid public key received.")
            return JsonResponse({'error': 'Invalid public key or Signature'}, status=412)

        try:
            pk.verify(base64.b64decode(signature), msg_body_bytes, ec.ECDSA(hashes.SHA1()))
            logger.info("Ebay Signature verified successfully")

            # TODO::::::
            # Remove items from database if seller_id matches, or Something like that.
            # could dump entire db as well if simpler

        except InvalidSignature:
            logger.warning("Invalid eBay signature")
            return JsonResponse({"error": "Invalid signature"}, status=412)

        # let ebay know it worked
        return HttpResponse(status=200)

    # if it fails make it known
    else:
        return HttpResponseBadRequest()

@csrf_exempt
@login_required
def ebay_get_items(request):

    context = {}
    # for blocking inappropriate searches
    flagged_any_item = False

    # when POSTing send our query info
    if request.method == "POST":

        logger.warning(f"Running Ebay Get items search")
        form = EbaySearchForm(request.POST)
        if form.is_valid():

            # set up url based on user input
            search_term = form.cleaned_data['search_term']
            # DEAR CHATGPT ADD ERROR CHECKING HERE
            item_count = form.cleaned_data['item_count']

            ebay_items_url = f"https://api.ebay.com/buy/browse/v1/item_summary/search?q={search_term}&limit={item_count}"
            try:
                oauth_access_token = get_oath_token()
                # send call to get some item data
                itemRequest = requests.get(url=ebay_items_url,
                                           headers = {
                                               'Authorization': f'Bearer {oauth_access_token}'
                                           },
                                           data = {})
                itemResponse = itemRequest.json()

                items = itemResponse.get("itemSummaries", [])

                # this is all per chatGPT to parse the json and get more item details
                parsed_items = []
                for item in items:
                    item_id = item.get("itemId")
                    # --- Second API call to get full item details (includes description) ---
                    detail_url = f"https://api.ebay.com/buy/browse/v1/item/{item_id}"
                    detail_response = requests.get(
                        url=detail_url,
                        headers={'Authorization': f'Bearer {oauth_access_token}'}
                    )

                    detail_data = detail_response.json()
                    description = detail_data.get("shortDescription")
                    if (description == None):
                        description = "Ebay Seller did not Provide Description for this item"

                    # when inappropriate items are found flag so we send an error message
                    if is_inappropriate(item.get("title")) or is_inappropriate(description):
                        flagged_any_item = True
                    else:
                        parsed_items.append({
                            "item_id": item_id,
                            "title": item.get("title"),
                            "price": f"{item['price']['value']} {item['price']['currency']}" if "price" in item else None,
                            "seller_username": item.get("seller", {}).get("username"),
                            "item_url": item.get("itemWebUrl"),
                            "image_url": item.get("image", {}).get("imageUrl"),
                            "description": description
                        })

                if flagged_any_item:
                    messages.warning(request, "Some inappropriate items were removed from search results")
                recent_items = []
                recent_items = parsed_items
                context['recent_items'] = recent_items

            # per chatGPT
            except Exception as e:
                logger.error(f"Error while calling eBay API: {e}")
                messages.error(request, "Unable to retrieve eBay items. Please try again later.")   # 🟩 new user-facing message
                form = EbaySearchForm()  # 🟩 reset form to empty
                context['form'] = form
                return render(request, "ebay_add_item.html", context)

    else:
        form = EbaySearchForm()  # empty form for GET request, no API stuff

    context['form'] = form

    return render(request, "ebay_add_item.html", context)

# get an ebay token from API
def get_oath_token():

    # build and send request with our secret variables in OS
    # get token response from API
    try:
        token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {EBAY_BASE64_AUTHORIZATION_TOKEN}"
        }
        token_scopes = "https://api.ebay.com/oauth/api_scope"
        token_data = {
            "grant_type": "client_credentials",
            "scope": token_scopes
        }
        tokenRequest = requests.post(
            url = token_url,
            headers = token_headers,
            data= token_data
        )
        logger.warning(f"--- ATTEMPTING TO GET OAUTH TOKEN ---:")
        # TESTING --- DO NOT UNCOMMENT IN MAIN CODE EVEN THO PROD TERMINAL IS PRIVATE ---
        #logger.warning(f"DEBUG: {tokenRequest.json}")
        #logger.warning(f"DEBUG: {EBAY_BASE64_AUTHORIZATION_TOKEN}")
        oauth_access_token = tokenRequest.json()['access_token']
        logger.warning(f"--- OAUTH ACCESS TOKEN SUCCESS ---:")
        return oauth_access_token

    # if it fails make it known
    except requests.RequestException as e:
        logger.error(f"OAuth token request failed: {e}")
        return None

    except KeyError:
        logger.error("OAuth token not found in response")
        return None

# ebay interactive item adding per chatGPT w ajax
@csrf_exempt
@require_POST
@login_required
def ajax_add_item(request):
    """
    Adds a single eBay item via AJAX without a redirect.
    Prevents duplicates using the eBay item_id.
    """
    try:
        # gets from parsed items somehow
        data = json.loads(request.body)
        title = data.get("title")
        description = data.get("description")
        image_url = data.get("image_url")
        item_id = data.get("item_id")  # ✅ new
        logger.warning(f"DATA:::  {data}")
        item_url = data.get("item_url")

        if not title or not description:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # ✅ Duplicate check based on eBay item_id
        if item_id and Item.objects.filter(item_id=item_id).exists():
            return JsonResponse({"error": "Item already exists in catalog."}, status=200)

        # ✅ Create new item only if not a duplicate
        item = Item.objects.create(
            title=title,
            description=description,
            image_url=image_url,
            tag="Accessory",
            item_id=item_id,  # ✅ new
            item_ebay_url = item_url
        )
        return JsonResponse({"message": "Item added successfully", "id": item.id})

    except Exception as e:
        logger.error(f"Error adding item: {e}")
        return JsonResponse({"error": str(e)}, status=500)

# filter so nsfw stuff won't be added from ebay if a user searches for it, and block searches too
def is_inappropriate(text):
    if not text:
        return False
    else:
        # using adult.txt file as the word blacklist basically
        content_filter = SafeText(
            language='en',
            custom_words_dir='/content_filters'
        )
        # also checks some basic profanity
        matches = content_filter.check_profanity(text)
        return bool(matches)