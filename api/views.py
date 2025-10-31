from django.shortcuts import render
import hashlib
import json
from django.http import (
    HttpResponse,
    JsonResponse,
    HttpResponseBadRequest
)
import os
import base64
from django.views.decorators.csrf import csrf_exempt

# super based on https://stackoverflow.com/questions/68569773/ebay-marketplace-account-deletion-closure-notifications
EBAY_VERIFICATION_TOKEN = os.environ.get('EBAY_VERIFICATION_TOKEN')
# need to have this to support accepting requests to delete data from Ebay users who delete accounts.
@csrf_exempt
def ebay_marketplace_deletion_notification(request):
    challengeCode = request.GET.get('challenge_code')
    X_EBAY_SIGNATURE = 'X-Ebay-Signature'
    EBAY_BASE64_AUTHORIZATION_TOKEN = "" # CALCULATE FROM CLIENT:ID CLIENT:SECRET OR SOMETHING

    # reply to challengecode basically just saying "yeah we got it"
    if challengeCode is not None:
        verificationToken = EBAY_VERIFICATION_TOKEN # random 32-80 char string
        endpoint_url = "https://best-dressed.net/auth/ebay_market_delete/"
        m = hashlib.sha256((challengeCode + verificationToken + endpoint_url).encode('utf-8'))
        return JsonResponse({"challengeResponse": m.hexdigest()}, status=200)

    # when ebay sends their delete request verify it with public key then delete
    elif request.method == 'POST':
        # the ebay signature is a json body encoded so once we decode we access its elements
        #x_ebay_signature = request.headers[X_EBAY_SIGNATURE]
        #x_ebay_signature_decoded = json.loads(base64.b64decode(x_ebay_signature).decode('utf-8'))
        # then the key and allat is passed which we query from api or something
        #kid = x_ebay_signature_decoded['kid']
        #signature = x_ebay_signature_decoded['signature']

        # do some other stuff to validate that it came from ebay
        # Remove items from database if seller_id matches, or Something like that.
        return HttpResponse(status=200) # PLACEHOLDER
    else:
        return HttpResponseBadRequest()