import hashlib
import hmac
import json
import time
from typing import Literal
from urllib.parse import urlparse

from .constants import (
    APP_VERSION,
    PLATFORM,
    WEB_APP_VERSION,
    WEB_PLATFORM,
)


def generate_signature(
    token: str,
    path: str,
    body_or_query: str,
    device_id: str,
) -> tuple[str, dict[str, str]]:
    """Generate signature for Skland API request.

    The signature algorithm:
    1. Construct the string: path + body_or_query + timestamp + header_json
    2. HMAC-SHA256 with token as key
    3. MD5 the result

    Args:
        token: The token obtained from generate_cred_by_code (not the cred)
        path: The request path (without host, e.g., "/api/v1/game/player/info")
        body_or_query: Query string for GET requests, JSON body for POST requests
        timestamp: Unix timestamp (defaults to current time - 2 seconds)
        device_id: Device ID (defaults to DEFAULT_DEVICE_ID)

    Returns:
        A tuple of (signature, header_dict) where header_dict contains
        platform, timestamp, dId, and vName.
    """
    timestamp = int(time.time()) - 2
    timestamp_str = str(timestamp)

    # Header for signature - order matters!
    header_for_sign: dict[str, str] = {
        "platform": PLATFORM,
        "timestamp": timestamp_str,
        "dId": device_id,
        "vName": APP_VERSION,
    }

    # Construct the string to sign
    header_json = json.dumps(header_for_sign, separators=(",", ":"))
    sign_string = path + body_or_query + timestamp_str + header_json

    # HMAC-SHA256
    token_bytes = token.encode("utf-8")
    sign_bytes = sign_string.encode("utf-8")
    hmac_result = hmac.new(token_bytes, sign_bytes, hashlib.sha256).hexdigest()

    # MD5
    signature = hashlib.md5(hmac_result.encode("utf-8")).hexdigest()

    return signature, header_for_sign


def get_signed_headers(
    url: str,
    method: Literal["GET", "POST"],
    body: dict | None,
    base_headers: dict[str, str],
    sign_token: str,
    cred: str,
    device_id: str,
) -> dict[str, str]:
    """Generate signed headers for a Skland API request.

    Args:
        url: The full URL of the request
        method: HTTP method ("GET" or "POST")
        body: Request body for POST requests, None for GET requests
        base_headers: Base headers to include
        sign_token: Token for signature generation
        cred: Credential token to include in headers
        device_id: Device ID for signature

    Returns:
        Complete headers dict with signature and all required fields.
    """
    headers = base_headers.copy()
    headers["cred"] = cred

    # Parse URL
    parsed = urlparse(url)
    path = parsed.path

    # Determine body_or_query based on method
    if method == "GET":
        body_or_query = parsed.query or ""
    else:
        body_or_query = json.dumps(body, separators=(",", ":")) if body else ""

    # Generate signature
    signature, sign_headers = generate_signature(
        token=sign_token,
        path=path,
        body_or_query=body_or_query,
        device_id=device_id,
    )

    # Add signature and sign headers
    headers["sign"] = signature
    headers.update(sign_headers)

    return headers


def generate_web_signature(
    token: str,
    path: str,
    body_or_query: str,
    device_id: str,
) -> tuple[str, dict[str, str]]:
    """Generate signature for Skland web API request.

    The web API uses lowercase header keys and platform 3.

    Args:
        token: The token obtained from generate_cred_by_code (not the cred)
        path: The request path (without host, e.g., "/web/v1/auth/refresh")
        body_or_query: Query string for GET requests, JSON body for POST requests
        timestamp: Unix timestamp (defaults to current time - 2 seconds)
        device_id: Device ID (defaults to DEFAULT_DEVICE_ID)

    Returns:
        A tuple of (signature, header_dict) where header_dict contains
        platform, timestamp, did, and vname (lowercase keys).
    """
    timestamp = int(time.time()) - 2
    timestamp_str = str(timestamp)

    # Header for signature - order matters! Web API uses lowercase keys
    header_for_sign: dict[str, str] = {
        "platform": WEB_PLATFORM,
        "timestamp": timestamp_str,
        "dId": device_id,
        "vName": WEB_APP_VERSION,
    }

    # Construct the string to sign
    header_json = json.dumps(header_for_sign, separators=(",", ":"))
    sign_string = path + body_or_query + timestamp_str + header_json

    # HMAC-SHA256
    token_bytes = token.encode("utf-8")
    sign_bytes = sign_string.encode("utf-8")
    hmac_result = hmac.new(token_bytes, sign_bytes, hashlib.sha256).hexdigest()

    # MD5
    signature = hashlib.md5(hmac_result.encode("utf-8")).hexdigest()

    # Return headers with lowercase keys for web API
    web_headers: dict[str, str] = {
        "platform": WEB_PLATFORM,
        "timestamp": timestamp_str,
        "did": device_id,
        "vname": WEB_APP_VERSION,
    }

    return signature, web_headers


def get_web_signed_headers(
    url: str,
    method: Literal["GET", "POST"],
    body: dict | None,
    base_headers: dict[str, str],
    old_token: str,
    cred: str,
    device_id: str,
) -> dict[str, str]:
    headers = base_headers.copy()
    headers["cred"] = cred

    # Parse URL
    parsed = urlparse(url)
    path = parsed.path

    # Determine body_or_query based on method
    if method == "GET":
        body_or_query = parsed.query or ""
    else:
        body_or_query = json.dumps(body, separators=(",", ":")) if body else ""

    # Generate signature
    signature, sign_headers = generate_web_signature(
        token=old_token,
        path=path,
        body_or_query=body_or_query,
        device_id=device_id,
    )

    # Add signature and sign headers
    headers["sign"] = signature
    headers.update(sign_headers)

    return headers
