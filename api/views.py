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
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

logger = logging.getLogger(__name__)

# heavily based on https://stackoverflow.com/questions/68569773/ebay-marketplace-account-deletion-closure-notifications
# and some chatGPT code for signature verification and request simulation/testing
EBAY_VERIFICATION_TOKEN = os.environ.get('EBAY_VERIFICATION_TOKEN')
EBAY_BASE64_AUTHORIZATION_TOKEN = os.environ.get("EBAY_BASE64_AUTHORIZATION_TOKEN") # CALCULATE FROM CLIENT:ID CLIENT:SECRET OR SOMETHING
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
        logger.warning(f"AUTHTOKEN: {EBAY_BASE64_AUTHORIZATION_TOKEN}")


        # get public key for verification
        # https://developer.ebay.com/api-docs/commerce/notification/resources/public_key/methods/getPublicKey
        public_key = None
        try:


            token_url = "https://api.ebay.com/identity/v1/oauth2/token"
            #token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
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
                                    token_url,
                                    headers = token_headers,
                                    data= token_data
                                    )

            logger.warning(f"TOKEN URL: {token_url}")
            logger.warning(f"HEADERS: {token_headers}")
            logger.warning(f"DATA: {token_data}")
            logger.warning(f"MADE IT THIS FAR DIDNT BREAK {tokenRequest.json()} {tokenRequest}")
            oauth_access_token = tokenRequest.json()['access_token']
            logger.warning(f"OAUTH ACCESS TOKEN: {oauth_access_token}")


            # send out a call to get public key
            ebay_verification_url = f'https://api.ebay.com/commerce/notification/v1/public_key/{kid}'
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
            return JsonResponse({}, status=500)

        # if we get here we have the public key and everything from ebay,
        # so use it to verify signature actually came from eBay
        pk = public_key
        msg_body_bytes = request.body
        public_key_pem = pk.encode("utf-8")
        pk = serialization.load_pem_public_key(public_key_pem)
        try:
            pk.verify(base64.b64decode(signature), msg_body_bytes, ec.ECDSA(hashes.SHA1()))
            logger.info("Ebay Signature verified successfully")

        except InvalidSignature:
            logger.warning("Invalid eBay signature")
            return JsonResponse({"error": "Invalid signature"}, status=412)

        # Remove items from database if seller_id matches, or Something like that.

        # let ebay know it worked
        return HttpResponse(status=200)
    else:
        return HttpResponseBadRequest()