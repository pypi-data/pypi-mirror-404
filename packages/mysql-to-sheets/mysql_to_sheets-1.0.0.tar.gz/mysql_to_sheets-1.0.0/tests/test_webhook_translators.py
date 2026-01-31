"""Tests for MoR (Merchant of Record) webhook translators.

Tests cover:
- Event mapping for Lemon Squeezy, Paddle, and 2Checkout
- Signature verification
- Payload translation to internal billing format
"""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest


class TestLemonSqueezyTranslator:
    """Tests for the Lemon Squeezy webhook translator."""

    def test_translate_subscription_created(self):
        """Verify subscription_created event translation."""
        from examples.lemonsqueezy_webhook_translator import translate_event

        event = {
            "meta": {
                "event_name": "subscription_created",
                "custom_data": {"org_slug": "acme", "organization_id": "123"},
            },
            "data": {
                "id": "sub_123",
                "attributes": {
                    "status": "active",
                    "customer_id": 456,
                    "variant_id": 789,
                    "renews_at": "2024-02-15T10:30:00Z",
                    "product_name": "Pro Monthly",
                },
            },
        }

        result = translate_event(event)

        assert result is not None
        assert result["event"] == "subscription.created"
        assert result["data"]["billing_status"] == "active"
        assert result["data"]["billing_customer_id"] == "456"
        assert result["data"]["organization_slug"] == "acme"
        assert result["data"]["organization_id"] == 123
        assert result["data"]["subscription_tier"] == "pro"
        assert result["data"]["subscription_period_end"] == "2024-02-15T10:30:00Z"

    def test_translate_subscription_cancelled(self):
        """Verify subscription_cancelled event translation."""
        from examples.lemonsqueezy_webhook_translator import translate_event

        event = {
            "meta": {"event_name": "subscription_cancelled", "custom_data": {}},
            "data": {
                "id": "sub_123",
                "attributes": {"status": "cancelled", "customer_id": 456},
            },
        }

        result = translate_event(event)

        assert result is not None
        assert result["event"] == "subscription.canceled"
        assert result["data"]["billing_status"] == "canceled"

    def test_translate_payment_success(self):
        """Verify subscription_payment_success event translation."""
        from examples.lemonsqueezy_webhook_translator import translate_event

        event = {
            "meta": {"event_name": "subscription_payment_success", "custom_data": {}},
            "data": {
                "id": "sub_123",
                "attributes": {"status": "active", "customer_id": 456},
            },
        }

        result = translate_event(event)

        assert result is not None
        assert result["event"] == "payment.succeeded"

    def test_translate_payment_failed(self):
        """Verify subscription_payment_failed event translation."""
        from examples.lemonsqueezy_webhook_translator import translate_event

        event = {
            "meta": {"event_name": "subscription_payment_failed", "custom_data": {}},
            "data": {
                "id": "sub_123",
                "attributes": {"status": "past_due", "customer_id": 456},
            },
        }

        result = translate_event(event)

        assert result is not None
        assert result["event"] == "payment.failed"
        assert result["data"]["billing_status"] == "past_due"

    def test_translate_unknown_event_returns_none(self):
        """Verify unknown events return None."""
        from examples.lemonsqueezy_webhook_translator import translate_event

        event = {
            "meta": {"event_name": "unknown_event", "custom_data": {}},
            "data": {"attributes": {}},
        }

        result = translate_event(event)
        assert result is None

    def test_verify_signature_valid(self):
        """Verify valid HMAC signature verification."""
        from examples.lemonsqueezy_webhook_translator import verify_signature

        payload = b'{"test": "data"}'
        secret = "test_secret"
        valid_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        assert verify_signature(payload, valid_sig, secret) is True

    def test_verify_signature_invalid(self):
        """Verify invalid signature detection."""
        from examples.lemonsqueezy_webhook_translator import verify_signature

        payload = b'{"test": "data"}'
        secret = "test_secret"

        assert verify_signature(payload, "invalid_signature", secret) is False

    def test_tier_extraction_from_product_name(self):
        """Verify tier is extracted from product name when variant not mapped."""
        from examples.lemonsqueezy_webhook_translator import translate_event

        for tier_keyword, expected_tier in [
            ("Enterprise Plan", "enterprise"),
            ("Business Monthly", "business"),
            ("Pro Yearly", "pro"),
        ]:
            event = {
                "meta": {"event_name": "subscription_created", "custom_data": {}},
                "data": {
                    "attributes": {
                        "status": "active",
                        "customer_id": 1,
                        "variant_id": 999,  # Not in tier map
                        "product_name": tier_keyword,
                    }
                },
            }

            result = translate_event(event)
            assert result["data"]["subscription_tier"] == expected_tier

    def test_status_mapping(self):
        """Verify all Lemon Squeezy statuses are mapped correctly."""
        from examples.lemonsqueezy_webhook_translator import _map_status

        mappings = {
            "on_trial": "trialing",
            "active": "active",
            "paused": "paused",
            "past_due": "past_due",
            "unpaid": "past_due",
            "cancelled": "canceled",
            "expired": "canceled",
        }

        for ls_status, expected in mappings.items():
            assert _map_status(ls_status) == expected


class TestPaddleTranslator:
    """Tests for the Paddle webhook translator."""

    def test_translate_subscription_created(self):
        """Verify subscription.created event translation."""
        from examples.paddle_webhook_translator import translate_event

        event = {
            "event_id": "evt_123",
            "event_type": "subscription.created",
            "occurred_at": "2024-01-15T10:30:00Z",
            "data": {
                "id": "sub_123",
                "status": "active",
                "customer_id": "ctm_456",
                "items": [
                    {
                        "price": {
                            "id": "pri_pro_monthly",
                            "product": {"name": "Pro Plan"},
                        }
                    }
                ],
                "current_billing_period": {"ends_at": "2024-02-15T10:30:00Z"},
                "custom_data": {"org_slug": "acme", "organization_id": "123"},
            },
        }

        result = translate_event(event)

        assert result is not None
        assert result["event"] == "subscription.created"
        assert result["data"]["billing_status"] == "active"
        assert result["data"]["billing_customer_id"] == "ctm_456"
        assert result["data"]["organization_slug"] == "acme"
        assert result["data"]["organization_id"] == 123
        assert result["data"]["subscription_tier"] == "pro"
        assert result["data"]["subscription_period_end"] == "2024-02-15T10:30:00Z"

    def test_translate_subscription_canceled(self):
        """Verify subscription.canceled event translation."""
        from examples.paddle_webhook_translator import translate_event

        event = {
            "event_type": "subscription.canceled",
            "occurred_at": "2024-01-15T10:30:00Z",
            "data": {
                "id": "sub_123",
                "status": "canceled",
                "customer_id": "ctm_456",
            },
        }

        result = translate_event(event)

        assert result is not None
        assert result["event"] == "subscription.canceled"
        assert result["data"]["billing_status"] == "canceled"

    def test_translate_transaction_completed(self):
        """Verify transaction.completed event translation."""
        from examples.paddle_webhook_translator import translate_event

        event = {
            "event_type": "transaction.completed",
            "occurred_at": "2024-01-15T10:30:00Z",
            "data": {
                "id": "txn_123",
                "subscription_id": "sub_456",
                "customer_id": "ctm_789",
                "items": [
                    {
                        "price": {
                            "id": "pri_business_monthly",
                            "product": {"name": "Business Plan"},
                        }
                    }
                ],
                "custom_data": {"org_slug": "acme"},
            },
        }

        result = translate_event(event)

        assert result is not None
        assert result["event"] == "payment.succeeded"
        assert result["data"]["billing_status"] == "active"
        assert result["data"]["subscription_tier"] == "business"

    def test_translate_transaction_payment_failed(self):
        """Verify transaction.payment_failed event translation."""
        from examples.paddle_webhook_translator import translate_event

        event = {
            "event_type": "transaction.payment_failed",
            "occurred_at": "2024-01-15T10:30:00Z",
            "data": {
                "id": "txn_123",
                "customer_id": "ctm_789",
            },
        }

        result = translate_event(event)

        assert result is not None
        assert result["event"] == "payment.failed"
        assert result["data"]["billing_status"] == "past_due"

    def test_translate_unknown_event_returns_none(self):
        """Verify unknown events return None."""
        from examples.paddle_webhook_translator import translate_event

        event = {"event_type": "unknown.event", "data": {}}

        result = translate_event(event)
        assert result is None

    def test_verify_signature_valid(self):
        """Verify valid Paddle signature verification."""
        from examples.paddle_webhook_translator import verify_signature

        payload = b'{"test": "data"}'
        secret = "test_secret"
        timestamp = "1234567890"

        signed_payload = f"{timestamp}:{payload.decode()}"
        valid_sig = hmac.new(
            secret.encode(), signed_payload.encode(), hashlib.sha256
        ).hexdigest()
        signature = f"ts={timestamp};h1={valid_sig}"

        assert verify_signature(payload, signature, secret) is True

    def test_verify_signature_invalid(self):
        """Verify invalid signature detection."""
        from examples.paddle_webhook_translator import verify_signature

        payload = b'{"test": "data"}'
        secret = "test_secret"
        signature = "ts=1234567890;h1=invalid"

        assert verify_signature(payload, signature, secret) is False

    def test_verify_signature_empty(self):
        """Verify empty signature returns False."""
        from examples.paddle_webhook_translator import verify_signature

        assert verify_signature(b"data", "", "secret") is False

    def test_tier_extraction_from_product_name(self):
        """Verify tier is extracted from product name when price not mapped."""
        from examples.paddle_webhook_translator import translate_event

        for product_name, expected_tier in [
            ("Enterprise Plan", "enterprise"),
            ("Business Monthly", "business"),
            ("Pro Yearly", "pro"),
        ]:
            event = {
                "event_type": "subscription.created",
                "data": {
                    "status": "active",
                    "customer_id": "ctm_1",
                    "items": [
                        {
                            "price": {
                                "id": "pri_unknown",  # Not in tier map
                                "product": {"name": product_name},
                            }
                        }
                    ],
                },
            }

            result = translate_event(event)
            assert result["data"]["subscription_tier"] == expected_tier

    def test_status_mapping_with_event_override(self):
        """Verify event type overrides status mapping."""
        from examples.paddle_webhook_translator import _map_status

        # past_due event should override status
        assert _map_status("active", "subscription.past_due") == "past_due"
        assert _map_status("active", "subscription.canceled") == "canceled"


class TestTwoCheckoutTranslator:
    """Tests for the 2Checkout webhook translator."""

    def test_translate_order_created_recurring(self):
        """Verify ORDER_CREATED event translation for recurring orders."""
        from examples.twocheckout_webhook_translator import translate_ipn

        ipn_data = {
            "message_type": "ORDER_CREATED",
            "recurring": "1",
            "sale_id": "123456",
            "item_id_1": "pro_monthly",
            "item_name_1": "Pro Plan Monthly",
            "customer_email": "user@example.com",
            "custom_org_slug": "acme",
            "custom_organization_id": "123",
            "next_payment_date": "2024-02-15",
        }

        result = translate_ipn(ipn_data)

        assert result is not None
        assert result["event"] == "subscription.created"
        assert result["data"]["billing_status"] == "active"
        assert result["data"]["billing_customer_id"] == "123456"
        assert result["data"]["organization_slug"] == "acme"
        assert result["data"]["organization_id"] == 123
        assert result["data"]["subscription_tier"] == "pro"
        assert "2024-02-15" in result["data"]["subscription_period_end"]

    def test_translate_order_created_non_recurring_returns_none(self):
        """Verify ORDER_CREATED for non-recurring orders returns None."""
        from examples.twocheckout_webhook_translator import translate_ipn

        ipn_data = {
            "message_type": "ORDER_CREATED",
            "recurring": "0",  # Not recurring
            "sale_id": "123456",
        }

        result = translate_ipn(ipn_data)
        assert result is None

    def test_translate_recurring_installment_success(self):
        """Verify RECURRING_INSTALLMENT_SUCCESS event translation."""
        from examples.twocheckout_webhook_translator import translate_ipn

        ipn_data = {
            "message_type": "RECURRING_INSTALLMENT_SUCCESS",
            "sale_id": "123456",
            "item_name_1": "Business Plan",
            "custom_org_slug": "acme",
        }

        result = translate_ipn(ipn_data)

        assert result is not None
        assert result["event"] == "payment.succeeded"
        assert result["data"]["billing_status"] == "active"
        assert result["data"]["subscription_tier"] == "business"

    def test_translate_recurring_installment_failed(self):
        """Verify RECURRING_INSTALLMENT_FAILED event translation."""
        from examples.twocheckout_webhook_translator import translate_ipn

        ipn_data = {
            "message_type": "RECURRING_INSTALLMENT_FAILED",
            "sale_id": "123456",
        }

        result = translate_ipn(ipn_data)

        assert result is not None
        assert result["event"] == "payment.failed"
        assert result["data"]["billing_status"] == "past_due"

    def test_translate_recurring_stopped(self):
        """Verify RECURRING_STOPPED event translation."""
        from examples.twocheckout_webhook_translator import translate_ipn

        ipn_data = {
            "message_type": "RECURRING_STOPPED",
            "sale_id": "123456",
        }

        result = translate_ipn(ipn_data)

        assert result is not None
        assert result["event"] == "subscription.canceled"
        assert result["data"]["billing_status"] == "canceled"

    def test_translate_unknown_event_returns_none(self):
        """Verify unknown IPN types return None."""
        from examples.twocheckout_webhook_translator import translate_ipn

        ipn_data = {"message_type": "UNKNOWN_TYPE", "sale_id": "123456"}

        result = translate_ipn(ipn_data)
        assert result is None

    def test_parse_ipn_data_json(self):
        """Verify JSON IPN data parsing."""
        from examples.twocheckout_webhook_translator import parse_ipn_data

        json_data = b'{"message_type": "ORDER_CREATED", "sale_id": "123"}'
        result = parse_ipn_data(json_data)

        assert result["message_type"] == "ORDER_CREATED"
        assert result["sale_id"] == "123"

    def test_parse_ipn_data_form_encoded(self):
        """Verify form-encoded IPN data parsing."""
        from examples.twocheckout_webhook_translator import parse_ipn_data

        form_data = b"message_type=ORDER_CREATED&sale_id=123&recurring=1"
        result = parse_ipn_data(form_data)

        assert result["message_type"] == "ORDER_CREATED"
        assert result["sale_id"] == "123"
        assert result["recurring"] == "1"

    def test_tier_extraction_from_item_name(self):
        """Verify tier is extracted from item name when ID not mapped."""
        from examples.twocheckout_webhook_translator import translate_ipn

        for item_name, expected_tier in [
            ("Enterprise Subscription", "enterprise"),
            ("Business Monthly Plan", "business"),
            ("Pro Yearly", "pro"),
            ("Professional Plan", "pro"),
        ]:
            ipn_data = {
                "message_type": "RECURRING_INSTALLMENT_SUCCESS",
                "sale_id": "123",
                "item_name_1": item_name,
            }

            result = translate_ipn(ipn_data)
            assert result["data"]["subscription_tier"] == expected_tier

    def test_verify_signature_sha256(self):
        """Verify SHA256 signature verification."""
        from examples.twocheckout_webhook_translator import (
            _build_hash_string,
            verify_signature,
        )

        ipn_data = {"message_type": "ORDER_CREATED", "sale_id": "123"}
        secret = "test_secret"

        hash_string = _build_hash_string(ipn_data, secret)
        valid_hash = hmac.new(
            secret.encode(), hash_string.encode(), hashlib.sha256
        ).hexdigest()

        ipn_data["HASH"] = valid_hash.upper()

        assert verify_signature(ipn_data, secret) is True

    def test_verify_signature_invalid(self):
        """Verify invalid signature detection."""
        from examples.twocheckout_webhook_translator import verify_signature

        ipn_data = {
            "message_type": "ORDER_CREATED",
            "sale_id": "123",
            "HASH": "invalid_hash",
        }

        assert verify_signature(ipn_data, "test_secret") is False

    def test_verify_signature_missing_hash(self):
        """Verify missing HASH returns False."""
        from examples.twocheckout_webhook_translator import verify_signature

        ipn_data = {"message_type": "ORDER_CREATED", "sale_id": "123"}

        assert verify_signature(ipn_data, "test_secret") is False


class TestSignPayload:
    """Test the sign_payload function across all translators."""

    def test_sign_payload_consistency(self):
        """Verify all translators produce consistent signatures."""
        from examples.lemonsqueezy_webhook_translator import (
            sign_payload as ls_sign,
        )
        from examples.paddle_webhook_translator import sign_payload as paddle_sign
        from examples.twocheckout_webhook_translator import (
            sign_payload as twoco_sign,
        )

        payload = {"event": "subscription.created", "data": {"tier": "pro"}}
        secret = "test_secret"

        # All should produce the same format
        ls_sig = ls_sign(payload, secret)
        paddle_sig = paddle_sign(payload, secret)
        twoco_sig = twoco_sign(payload, secret)

        assert ls_sig.startswith("sha256=")
        assert paddle_sig.startswith("sha256=")
        assert twoco_sig.startswith("sha256=")

        # All should produce the same signature for the same input
        assert ls_sig == paddle_sig == twoco_sig
