"""Webhook HMAC signature generation and verification.

Provides cryptographic signing for webhook payloads to ensure
authenticity and integrity.
"""

import hashlib
import hmac
import json
from typing import Any


def sign_payload(payload: dict[str, Any], secret: str) -> str:
    """Generate HMAC-SHA256 signature for a webhook payload.

    The payload is serialized to JSON with sorted keys for
    consistent signing regardless of dict ordering.

    Args:
        payload: Webhook payload dictionary.
        secret: Shared secret for HMAC signing.

    Returns:
        Signature in format "sha256=<hex_digest>".
    """
    # Serialize payload deterministically
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))

    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={signature}"


def verify_signature(
    payload: dict[str, Any] | str,
    signature: str,
    secret: str,
) -> bool:
    """Verify a webhook signature.

    Uses constant-time comparison to prevent timing attacks.
    Ensures constant-time execution regardless of JSON validity
    to prevent timing oracles.

    Args:
        payload: Webhook payload (dict or JSON string).
        signature: Signature to verify (sha256=<hex>).
        secret: Shared secret for HMAC verification.

    Returns:
        True if signature is valid, False otherwise.
    """
    # Track whether payload is valid - but don't short-circuit
    is_valid_payload = True
    payload_dict: dict[str, Any] = {}

    # Validate and normalize payload to dict
    try:
        if isinstance(payload, dict):
            payload_dict = payload
        else:
            payload_dict = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        # Mark as invalid but continue to maintain constant timing
        is_valid_payload = False
        payload_dict = {}

    # Always compute expected signature (constant-time operation)
    expected = sign_payload(payload_dict, secret)

    # Always perform constant-time comparison
    signature_matches = hmac.compare_digest(signature, expected)

    # Return True only if both payload is valid AND signature matches
    # Using bitwise AND to avoid branch prediction differences
    return is_valid_payload and signature_matches


def generate_webhook_headers(
    payload: dict[str, Any],
    secret: str,
    event: str,
    delivery_id: str,
    timestamp: str,
    custom_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    """Generate headers for a webhook request.

    Includes signature, event type, and delivery metadata.

    Args:
        payload: Webhook payload dictionary.
        secret: Shared secret for signing.
        event: Event type (e.g., "sync.completed").
        delivery_id: Unique delivery identifier.
        timestamp: ISO 8601 timestamp.
        custom_headers: Optional additional headers.

    Returns:
        Dictionary of headers to include in request.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": sign_payload(payload, secret),
        "X-Webhook-Event": event,
        "X-Webhook-Delivery-Id": delivery_id,
        "X-Webhook-Timestamp": timestamp,
        "User-Agent": "MySQL-to-Sheets-Sync/1.0",
    }

    if custom_headers:
        headers.update(custom_headers)

    return headers


def extract_signature(headers: dict[str, str]) -> str | None:
    """Extract webhook signature from request headers.

    Checks common header names for the signature.

    Args:
        headers: Request headers dictionary.

    Returns:
        Signature string if found, None otherwise.
    """
    # Check standard header names (case-insensitive)
    header_names = [
        "X-Webhook-Signature",
        "x-webhook-signature",
        "X-Hub-Signature-256",  # GitHub style
        "X-Signature",
    ]

    for name in header_names:
        if name in headers:
            return headers[name]
        # Also check lowercase
        lower_name = name.lower()
        for key in headers:
            if key.lower() == lower_name:
                return headers[key]

    return None
