from django.shortcuts import render
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
import logging
import cryptography

logger = logging.getLogger(__name__)

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
        x_ebay_signature = request.headers["X-Ebay-Signature"]
        x_ebay_signature_decoded = json.loads(base64.b64decode(x_ebay_signature).decode('utf-8'))
        kid = x_ebay_signature_decoded['kid']
        signature = x_ebay_signature_decoded['signature']

        # get public key for verification
        # https://developer.ebay.com/api-docs/commerce/notification/resources/public_key/methods/getPublicKey
        public_key = None
        try:
            ebay_verification_url = f'https://api.ebay.com/commerce/notification/v1/public_key/{kid}'
            tokenRequest = requests.post(url='https://api.ebay.com/identity/vi/oauth2/token',
                                    headers = {
                                        'Content-Type': 'application/x-www-form-urlencoded',
                                        'Authorization': f"Basic {EBAY_BASE64_AUTHORIZATION_TOKEN}"
                                    },
                                    data='grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope')
            oauth_access_token = tokenRequest.json()['access_token']

            pkRequest = requests.get(url=ebay_verification_url,
                                            headers = {
                                                'Authorization': f'Bearer {oauth_access_token}'
                                            },
                                            data = {})
            if pkRequest.status_code == 200:
                pkResponse = pkRequest.json()
                public_key = pkResponse['key']


        # catch errors
        except Exception as e:
            message_title = f"Ebay Marketplace Account Deletion: Error performing validation"
            logger.error(f"{message_title} Error: {e}")
            return JsonResponse({}, status=HttpResponse(status=500))


        # Remove items from database if seller_id matches, or Something like that.

        # let ebay know it worked
        return HttpResponse(status=200)
    else:
        return HttpResponseBadRequest()