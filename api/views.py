"""
Views associated with API actions such as
item adding via ebay and some general item listing stuff.
"""
import hashlib
import json
import os
import base64
import logging

from django.shortcuts import render
from django.contrib import messages
from django.http import (
    HttpResponse,
    JsonResponse,
    HttpResponseBadRequest
)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

import requests

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature, InvalidKey

from safetext import SafeText

from best_dressed_app.models import Item
from .forms import EbaySearchForm

logger = logging.getLogger(__name__)

## Basically a giant amalgamation of
# pylint: disable=line-too-long
# https://stackoverflow.com/questions/68569773/ebay-marketplace-account-deletion-closure-notifications
# pylint: enable=line-too-long
# and a bunch of chatGPT/Claude code for processing json,
# and adapting signature validation to use cryptography lib

EBAY_VERIFICATION_TOKEN = os.environ.get('EBAY_VERIFICATION_TOKEN')
EBAY_BASE64_AUTHORIZATION_TOKEN = os.environ.get(
    "EBAY_BASE64_AUTHORIZATION_TOKEN")

EBAY_URL = 'https://api.ebay.com/'


def _handle_challenge_code(challenge_code):
    """Handle eBay challenge code verification."""
    verification_token = EBAY_VERIFICATION_TOKEN  # random 32-80 char string
    endpoint_url = "https://best-dressed.net/auth/ebay_market_delete/"
    m = hashlib.sha256((challenge_code +
                        verification_token +
                        endpoint_url).encode('utf-8'))
    return JsonResponse({"challengeResponse": m.hexdigest()}, status=200)


def _fetch_ebay_public_key(kid, oauth_access_token):
    """Fetch public key from eBay API. Raises exceptions to caller."""
    ebay_verification_url = (EBAY_URL +
                             f'commerce/notification/v1/public_key/{kid}')
    pk_request = requests.get(
        url=ebay_verification_url,
        headers={
            'Authorization': f'Bearer {oauth_access_token}'
        },
        data={},
        timeout=10
    )
    if pk_request.status_code == 200:
        pk_response = pk_request.json()
        return pk_response['key']
    return None


def _verify_signature_and_process_deletion(request, signature, public_key):
    """Verify eBay signature and process account deletion."""
    msg_body_bytes = request.body
    public_key_pem = public_key.encode("utf-8")

    # figure this out later
    try:
        pk = serialization.load_pem_public_key(public_key_pem)
    except (ValueError, InvalidKey):
        logging.error("Invalid public key received.")
        return JsonResponse({'error':
                             'Invalid public key or Signature'}, status=412)

    try:
        pk.verify(base64.b64decode(signature),
                  msg_body_bytes, ec.ECDSA(hashes.SHA1()))
        logger.info("Ebay Signature verified successfully")

        deletion_payload = json.loads(request.body.decode("utf-8"))

        # Ebay sends "username" for marketplace data deletion
        ebay_username = deletion_payload.get("username")
        logger.warning("EBAY MARKETPLACE"
                       " DELETE REQUEST FOR USER: %s", ebay_username)

        if ebay_username:
            # Delete all items where seller_id matches this username
            deleted_count, _ = (Item.objects.filter(seller_id=ebay_username)
                                .delete())
            logger.warning("Deleted %s Item(s) "
                           "belonging to deleted eBay "
                           "user: %s", deleted_count, ebay_username)
        else:
            logger.error("Deletion payload missing 'username' field")

    except InvalidSignature:
        logger.warning("Invalid eBay signature")
        return JsonResponse({"error": "Invalid signature"}, status=412)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error("Error processing marketplace deletion payload: %s", e)
        return JsonResponse({"error": "Invalid deletion payload"}, status=400)

    # let ebay know it worked
    return HttpResponse(status=200)


# need to have this to support accepting requests
# to delete data from Ebay users who delete accounts.
@csrf_exempt
def ebay_marketplace_deletion_notification(request):
    """Handle eBay marketplace account
    deletion notifications with signature verification."""
    challenge_code = request.GET.get('challenge_code')

    # reply to challengecode basically just saying "yeah we got it"
    if challenge_code is not None:
        return _handle_challenge_code(challenge_code)

    # when ebay sends their delete request verify it with public key then delete
    if request.method == 'POST':
        # the ebay signature is a json body encoded
        # so once we decode we access its elements
        x_ebay_signature = request.headers["X-Ebay-Signature"]
        x_ebay_signature_decoded = json.loads(
            base64.b64decode(x_ebay_signature).decode('utf-8'))
        kid = x_ebay_signature_decoded['kid']
        signature = x_ebay_signature_decoded['signature']
        #logger.warning(f"SIGNATURE: {signature}")
        #logger.warning(f"kid: {kid}")

        # So maybe this works, but I really have no idea how to verify
        # it from eBay themselves.
        # pylint: disable=line-too-long
        # https://developer.ebay.com/api-docs/commerce/notification/resources/public_key/methods/getPublicKey
        # pylint: enable=line-too-long
        try:
            oauth_access_token = get_oath_token()
            # send out a call to get public key
            public_key = _fetch_ebay_public_key(kid, oauth_access_token)
            if not public_key:
                logger.error("Failed to fetch public key from eBay")
                return JsonResponse({}, status=500)

        # catch errors
        # pylint: disable=broad-exception-caught
        except Exception as e:
            message_title = ("Ebay Marketplace Account "
                             "Deletion: Error performing validation")
            logger.error("%s Error: %s", message_title, e)
            return JsonResponse({}, status=500)
        # pylint: enable=broad-exception-caught
        # if we get here we have the public key and everything from ebay,
        # so use it to verify signature actually came from eBay
        return _verify_signature_and_process_deletion(
            request, signature, public_key)

    # if it fails make it known
    return HttpResponseBadRequest()


def _parse_ebay_item(item, oauth_access_token):
    """Parse a single eBay item and fetch its details."""
    item_id = item.get("itemId")
    # --- Second API call to get full item details (includes description) ---
    detail_url = f"https://api.ebay.com/buy/browse/v1/item/{item_id}"
    detail_response = requests.get(
        url=detail_url,
        headers={'Authorization': f'Bearer {oauth_access_token}'},
        timeout=10
    )

    detail_data = detail_response.json()
    description = detail_data.get("shortDescription")
    # get image url from details because we already
    # pulled it and it is better than img url from search.
    image_url = detail_data.get("image", {}).get("imageUrl")

    # sometimes there is no desc so account for that
    if description is None:
        description = "Ebay Seller did not Provide Description for this item"

    return {
        "item_id": item_id,
        "title": item.get("title"),
        "price": (f"{item['price']['value']} {item['price']['currency']}"
                  if "price" in item else None),
        "seller_id": item.get("seller", {}).get("username"),
        "item_url": item.get("itemWebUrl"),
        "image_url": image_url,
        "description": description,
    }


def _fetch_and_parse_ebay_items(search_term, item_count):
    """Fetch items from eBay API and parse them."""
    ebay_items_url = (
        "https://api.ebay.com/buy/browse/v1/item_summary/"
        f"search?q={search_term}&limit={item_count}")
    oauth_access_token = get_oath_token()

    # send call to get some item data
    item_request = requests.get(
        url=ebay_items_url,
        headers={
            'Authorization': f'Bearer {oauth_access_token}'
        },
        data={},
        timeout=10
    )
    item_response = item_request.json()
    items = item_response.get("itemSummaries", [])

    # this is all per chatGPT to parse the json and get more item details
    parsed_items = []
    flagged_any_item = False

    for item in items:
        parsed_item = _parse_ebay_item(item, oauth_access_token)

        # when inappropriate items are found flag so we send an error message and dont add that item
        if (is_inappropriate(parsed_item.get("title"))
            or is_inappropriate(parsed_item.get("description"))):
            flagged_any_item = True
        else:
            parsed_items.append(parsed_item)

    return parsed_items, flagged_any_item


@csrf_exempt
@login_required
def ebay_get_items(request):
    """Search and retrieve items from eBay API with content filtering."""
    context = {}

    # when POSTing send our query info to ebay
    if request.method == "POST":

        logger.warning("Running Ebay Get items search")
        form = EbaySearchForm(request.POST)
        if form.is_valid():

            # set up url based on user input
            search_term = form.cleaned_data['search_term']
            item_count = form.cleaned_data['item_count']

            # Check if search term itself is inappropriate
            # before making API call
            if is_inappropriate(search_term):
                messages.warning(request, "Search term contains inappropriate "
                                 "content and will likely result in "
                                 "filtered items. "
                                 "Please try a different search term.")
                form = EbaySearchForm()  # reset form to empty
                context['form'] = form
                return render(request, "ebay_add_item.html", context)

            try:
                parsed_items, flagged_any_item = (
                    _fetch_and_parse_ebay_items(search_term, item_count))

                if flagged_any_item:
                    messages.warning(request,
                                     "Some inappropriate items "
                                     "were removed from search results")

                context['recent_items'] = parsed_items

            # per chatGPT
            except (requests.RequestException,
                    KeyError, json.JSONDecodeError) as e:
                logger.error("Error while calling eBay API: %s", e)
                messages.error(request,
                               "Unable to retrieve eBay items. "
                               "Please try again later.")
                form = EbaySearchForm()  # reset form to empty
                context['form'] = form
                return render(request, "ebay_add_item.html", context)

    else:
        form = EbaySearchForm()  # empty form for GET request, no API stuff

    context['form'] = form

    return render(request, "ebay_add_item.html", context)


# get an ebay token from API
def get_oath_token():
    """Retrieve OAuth access token from eBay API."""
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
        token_request = requests.post(
            url=token_url,
            headers=token_headers,
            data=token_data,
            timeout=10
        )
        logger.warning("--- ATTEMPTING TO GET OAUTH TOKEN ---:")
        # TESTING --- DO NOT UNCOMMENT IN MAIN
        # CODE EVEN THO PROD TERMINAL IS PRIVATE ---
        #logger.warning(f"DEBUG: {tokenRequest.json}")
        #logger.warning(f"DEBUG: {EBAY_BASE64_AUTHORIZATION_TOKEN}")
        oauth_access_token = token_request.json()['access_token']
        logger.warning("--- OAUTH ACCESS TOKEN SUCCESS ---:")
        return oauth_access_token

    # if it fails make it known
    except requests.RequestException as e:
        logger.error("OAuth token request failed: %s", e)
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
        # so this json is sent in the ajax JS script in ebay_add_item.html
        data = json.loads(request.body)
        #logger.warning(f"DATA:::  {data}")
        title = data.get("title")
        description = data.get("description")
        image_url = data.get("image_url")
        item_id = data.get("item_id")  # ✅ new

        item_url = data.get("item_url")
        seller_id = data.get("seller_id")

        if not title or not description:
            return JsonResponse(
                {"error": "Missing required fields"},
                status=400)

        # ✅ Duplicate check based on eBay item_id
        if item_id and Item.objects.filter(item_id=item_id).exists():
            return JsonResponse(
                {"error": "Item already exists in catalog."},
                status=200)

        # ✅ Create new item only if not a duplicate
        item = Item.objects.create(
            title=title,
            description=description,
            image_url=image_url,
            tag="Accessory",
            item_id=item_id,  # ✅ new
            item_ebay_url=item_url,
            seller_id=seller_id
        )
        return JsonResponse(
            {"message": "Item added successfully",
             "id": item.id})

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error("Error adding item: %s", e)
        return JsonResponse({"error": "Failed to add item due to internal error."}, status=500)


# filter so nsfw stuff won't be added from ebay if a user searches
# for it, and block searches too
def is_inappropriate(text):
    """Check if text contains inappropriate content using SafeText filter."""
    if not text:
        return False
    # using adult.txt file as the word blacklist basically
    content_filter = SafeText(
        language='en',
        custom_words_dir='/content_filters'
    )
    # also checks some basic profanity
    matches = content_filter.check_profanity(text)
    return bool(matches)
