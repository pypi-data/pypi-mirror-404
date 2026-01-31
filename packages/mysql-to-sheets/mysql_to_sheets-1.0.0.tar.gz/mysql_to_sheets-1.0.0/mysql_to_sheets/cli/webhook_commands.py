"""CLI commands for webhook management.

NOTE: Webhooks require BUSINESS tier or higher.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
from typing import Any

from mysql_to_sheets.cli.tier_check import require_cli_tier
from mysql_to_sheets.cli.utils import (
    get_tenant_db_path,
)
from mysql_to_sheets.cli.utils import (
    output_result as base_output_result,
)
from mysql_to_sheets.core.webhooks.delivery import (
    get_webhook_delivery_service,
)
from mysql_to_sheets.models.organizations import get_organization_repository
from mysql_to_sheets.models.webhooks import (
    VALID_EVENT_TYPES,
    WebhookSubscription,
    get_webhook_repository,
)


def output_result(data: dict[str, Any], format: str) -> None:
    """Output result in the specified format.

    Args:
        data: Result data dictionary.
        format: Output format ('text' or 'json').
    """
    base_output_result(
        data,
        format,
        entity_key="webhook",
        entity_fields=["id", "name", "url"],
    )


def add_webhook_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add webhook management subcommands.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    webhook_parser = subparsers.add_parser(
        "webhook",
        help="Manage webhook subscriptions (multi-tenant)",
    )
    webhook_subparsers = webhook_parser.add_subparsers(
        dest="webhook_command",
        help="Webhook commands",
    )

    # webhook create
    webhook_create = webhook_subparsers.add_parser(
        "create",
        help="Create a new webhook subscription",
    )
    webhook_create.add_argument(
        "--name",
        required=True,
        help="Webhook name",
    )
    webhook_create.add_argument(
        "--url",
        required=True,
        help="Webhook URL (must start with http:// or https://)",
    )
    webhook_create.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    webhook_create.add_argument(
        "--events",
        required=True,
        help=f"Comma-separated list of events. Valid: {', '.join(VALID_EVENT_TYPES)}",
    )
    webhook_create.add_argument(
        "--secret",
        help="HMAC signing secret (auto-generated if not provided)",
    )
    webhook_create.add_argument(
        "--headers",
        help='Custom headers as JSON (e.g., \'{"Authorization": "Bearer xxx"}\')',
    )
    webhook_create.add_argument(
        "--retry-count",
        type=int,
        default=3,
        help="Number of retry attempts (default: 3, max: 10)",
    )
    webhook_create.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # webhook list
    webhook_list = webhook_subparsers.add_parser(
        "list",
        help="List webhook subscriptions",
    )
    webhook_list.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    webhook_list.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include inactive webhooks",
    )
    webhook_list.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of webhooks to list",
    )
    webhook_list.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # webhook get
    webhook_get = webhook_subparsers.add_parser(
        "get",
        help="Get webhook details",
    )
    webhook_get.add_argument(
        "--id",
        type=int,
        required=True,
        help="Webhook ID",
    )
    webhook_get.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    webhook_get.add_argument(
        "--show-secret",
        action="store_true",
        help="Show the signing secret",
    )
    webhook_get.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # webhook update
    webhook_update = webhook_subparsers.add_parser(
        "update",
        help="Update a webhook subscription",
    )
    webhook_update.add_argument(
        "--id",
        type=int,
        required=True,
        help="Webhook ID to update",
    )
    webhook_update.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    webhook_update.add_argument(
        "--name",
        help="New webhook name",
    )
    webhook_update.add_argument(
        "--url",
        help="New webhook URL",
    )
    webhook_update.add_argument(
        "--events",
        help="New comma-separated list of events",
    )
    webhook_update.add_argument(
        "--secret",
        help="New signing secret",
    )
    webhook_update.add_argument(
        "--headers",
        help="New custom headers as JSON",
    )
    webhook_update.add_argument(
        "--retry-count",
        type=int,
        help="New retry count",
    )
    webhook_update.add_argument(
        "--enable",
        action="store_true",
        help="Enable the webhook",
    )
    webhook_update.add_argument(
        "--disable",
        action="store_true",
        help="Disable the webhook",
    )
    webhook_update.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # webhook delete
    webhook_delete = webhook_subparsers.add_parser(
        "delete",
        help="Delete a webhook subscription",
    )
    webhook_delete.add_argument(
        "--id",
        type=int,
        required=True,
        help="Webhook ID to delete",
    )
    webhook_delete.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    webhook_delete.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # webhook test
    webhook_test = webhook_subparsers.add_parser(
        "test",
        help="Send a test webhook",
    )
    webhook_test.add_argument(
        "--id",
        type=int,
        required=True,
        help="Webhook ID to test",
    )
    webhook_test.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    webhook_test.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # webhook deliveries
    webhook_deliveries = webhook_subparsers.add_parser(
        "deliveries",
        help="View delivery history for a webhook",
    )
    webhook_deliveries.add_argument(
        "--id",
        type=int,
        required=True,
        help="Webhook ID",
    )
    webhook_deliveries.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    webhook_deliveries.add_argument(
        "--status",
        choices=["pending", "success", "failed"],
        help="Filter by delivery status",
    )
    webhook_deliveries.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of deliveries to show",
    )
    webhook_deliveries.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


@require_cli_tier("webhooks")
def handle_webhook_command(args: argparse.Namespace) -> int:
    """Handle webhook management commands.

    Requires BUSINESS tier or higher license.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    db_path = get_tenant_db_path()

    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    if args.webhook_command == "create":
        return _handle_webhook_create(args, db_path)
    elif args.webhook_command == "list":
        return _handle_webhook_list(args, db_path)
    elif args.webhook_command == "get":
        return _handle_webhook_get(args, db_path)
    elif args.webhook_command == "update":
        return _handle_webhook_update(args, db_path)
    elif args.webhook_command == "delete":
        return _handle_webhook_delete(args, db_path)
    elif args.webhook_command == "test":
        return _handle_webhook_test(args, db_path)
    elif args.webhook_command == "deliveries":
        return _handle_webhook_deliveries(args, db_path)
    else:
        print("Error: No webhook command specified. Use --help for usage.")
        return 1


def _get_organization_id(org_slug: str, db_path: str) -> int | None:
    """Get organization ID from slug.

    Args:
        org_slug: Organization slug.
        db_path: Database path.

    Returns:
        Organization ID or None if not found.
    """
    org_repo = get_organization_repository(db_path)
    org = org_repo.get_by_slug(org_slug)
    return org.id if org else None


def _handle_webhook_create(args: argparse.Namespace, db_path: str) -> int:
    """Handle webhook create command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    # Parse events
    events = [e.strip() for e in args.events.split(",")]
    invalid_events = [e for e in events if e not in VALID_EVENT_TYPES]
    if invalid_events:
        output_result(
            {
                "success": False,
                "message": f"Invalid event types: {', '.join(invalid_events)}",
                "errors": [f"Valid events: {', '.join(VALID_EVENT_TYPES)}"],
            },
            args.output,
        )
        return 1

    # Parse custom headers
    headers = None
    if args.headers:
        try:
            headers = json.loads(args.headers)
        except json.JSONDecodeError as e:
            output_result(
                {
                    "success": False,
                    "message": f"Invalid headers JSON: {e}",
                },
                args.output,
            )
            return 1

    # Generate secret if not provided
    secret = args.secret or secrets.token_hex(32)

    webhook_repo = get_webhook_repository(db_path)

    webhook = WebhookSubscription(
        name=args.name,
        url=args.url,
        secret=secret,
        events=events,
        organization_id=org_id,
        headers=headers,
        retry_count=min(args.retry_count, 10),  # Max 10 retries
    )

    try:
        webhook = webhook_repo.create_subscription(webhook)

        # Include secret in output since it was just created
        result = {
            "success": True,
            "message": "Webhook created successfully",
            "webhook": webhook.to_dict(include_secret=True),
        }
        if not args.secret:
            result["note"] = "Secret was auto-generated. Save it now - it won't be shown again!"

        output_result(result, args.output)
        return 0
    except ValueError as e:
        output_result(
            {
                "success": False,
                "message": str(e),
            },
            args.output,
        )
        return 1


def _handle_webhook_list(args: argparse.Namespace, db_path: str) -> int:
    """Handle webhook list command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    webhook_repo = get_webhook_repository(db_path)
    webhooks = webhook_repo.get_all_subscriptions(
        organization_id=org_id,
        include_inactive=args.include_inactive,
        limit=args.limit,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "webhooks": [w.to_dict() for w in webhooks],
                    "total": len(webhooks),
                },
                indent=2,
            )
        )
    else:
        if not webhooks:
            print("No webhooks found.")
        else:
            print(f"Webhooks ({len(webhooks)} found):")
            print("-" * 80)
            for wh in webhooks:
                status = "active" if wh.is_active else "inactive"
                failures = f"({wh.failure_count} failures)" if wh.failure_count > 0 else ""
                print(f"  {wh.id:4d}  {wh.name:30s}  {status:10s}  {failures}")
                print(f"        URL: {wh.url[:60]}...")
                print(f"        Events: {', '.join(wh.events)}")

    return 0


def _handle_webhook_get(args: argparse.Namespace, db_path: str) -> int:
    """Handle webhook get command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    webhook_repo = get_webhook_repository(db_path)
    webhook = webhook_repo.get_subscription_by_id(args.id, organization_id=org_id)

    if not webhook:
        output_result(
            {
                "success": False,
                "message": f"Webhook with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    if args.output == "json":
        print(
            json.dumps(
                {"success": True, "webhook": webhook.to_dict(include_secret=args.show_secret)},
                indent=2,
            )
        )
    else:
        print(f"Webhook: {webhook.name}")
        print(f"  ID: {webhook.id}")
        print(f"  URL: {webhook.url}")
        print(f"  Status: {'Active' if webhook.is_active else 'Inactive'}")
        print(f"  Events: {', '.join(webhook.events)}")
        if args.show_secret:
            print(f"  Secret: {webhook.secret}")
        print(f"  Retry Count: {webhook.retry_count}")
        if webhook.headers:
            print(f"  Custom Headers: {webhook.headers}")
        print(f"  Created: {webhook.created_at.isoformat() if webhook.created_at else 'N/A'}")
        print(
            f"  Last Triggered: {webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else 'Never'}"
        )
        print(f"  Failure Count: {webhook.failure_count}")

    return 0


def _handle_webhook_update(args: argparse.Namespace, db_path: str) -> int:
    """Handle webhook update command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    webhook_repo = get_webhook_repository(db_path)
    webhook = webhook_repo.get_subscription_by_id(args.id, organization_id=org_id)

    if not webhook:
        output_result(
            {
                "success": False,
                "message": f"Webhook with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    # Apply updates
    if args.name:
        webhook.name = args.name
    if args.url:
        webhook.url = args.url
    if args.secret:
        webhook.secret = args.secret
    if args.events:
        events = [e.strip() for e in args.events.split(",")]
        invalid_events = [e for e in events if e not in VALID_EVENT_TYPES]
        if invalid_events:
            output_result(
                {
                    "success": False,
                    "message": f"Invalid event types: {', '.join(invalid_events)}",
                },
                args.output,
            )
            return 1
        webhook.events = events
    if args.retry_count is not None:
        webhook.retry_count = min(args.retry_count, 10)
    if args.enable:
        webhook.is_active = True
    if args.disable:
        webhook.is_active = False

    # Parse custom headers
    if args.headers:
        try:
            webhook.headers = json.loads(args.headers)
        except json.JSONDecodeError as e:
            output_result(
                {
                    "success": False,
                    "message": f"Invalid headers JSON: {e}",
                },
                args.output,
            )
            return 1

    try:
        webhook = webhook_repo.update_subscription(webhook)
        output_result(
            {
                "success": True,
                "message": "Webhook updated successfully",
                "webhook": webhook.to_dict(),
            },
            args.output,
        )
        return 0
    except ValueError as e:
        output_result(
            {
                "success": False,
                "message": str(e),
            },
            args.output,
        )
        return 1


def _handle_webhook_delete(args: argparse.Namespace, db_path: str) -> int:
    """Handle webhook delete command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    webhook_repo = get_webhook_repository(db_path)
    webhook = webhook_repo.get_subscription_by_id(args.id, organization_id=org_id)

    if not webhook:
        output_result(
            {
                "success": False,
                "message": f"Webhook with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    webhook_repo.delete_subscription(args.id, organization_id=org_id)

    output_result(
        {
            "success": True,
            "message": f"Webhook '{webhook.name}' has been deleted",
        },
        args.output,
    )
    return 0


def _handle_webhook_test(args: argparse.Namespace, db_path: str) -> int:
    """Handle webhook test command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    webhook_repo = get_webhook_repository(db_path)
    webhook = webhook_repo.get_subscription_by_id(args.id, organization_id=org_id)

    if not webhook:
        output_result(
            {
                "success": False,
                "message": f"Webhook with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    print(f"Sending test webhook to {webhook.url}...")

    try:
        delivery_service = get_webhook_delivery_service(db_path)
        result = delivery_service.test_subscription(webhook)

        if result.success:
            output_result(
                {
                    "success": True,
                    "message": "Test webhook delivered successfully",
                    "delivery": result.to_dict(),
                },
                args.output,
            )
            return 0
        else:
            output_result(
                {
                    "success": False,
                    "message": f"Test webhook delivery failed: {result.error_message}",
                    "delivery": result.to_dict(),
                },
                args.output,
            )
            return 1
    except Exception as e:
        output_result(
            {
                "success": False,
                "message": f"Failed to send test webhook: {e}",
            },
            args.output,
        )
        return 1


def _handle_webhook_deliveries(args: argparse.Namespace, db_path: str) -> int:
    """Handle webhook deliveries command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    webhook_repo = get_webhook_repository(db_path)

    # Verify webhook exists
    webhook = webhook_repo.get_subscription_by_id(args.id, organization_id=org_id)
    if not webhook:
        output_result(
            {
                "success": False,
                "message": f"Webhook with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    deliveries = webhook_repo.get_deliveries_for_subscription(
        sub_id=args.id,
        limit=args.limit,
        status=args.status,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "webhook_name": webhook.name,
                    "deliveries": [d.to_dict() for d in deliveries],
                    "total": len(deliveries),
                },
                indent=2,
            )
        )
    else:
        if not deliveries:
            print(f"No deliveries found for webhook '{webhook.name}'.")
        else:
            print(f"Deliveries for '{webhook.name}' ({len(deliveries)} found):")
            print("-" * 80)
            for d in deliveries:
                status_icon = "✓" if d.status == "success" else "✗" if d.status == "failed" else "…"
                timestamp = d.created_at.strftime("%Y-%m-%d %H:%M") if d.created_at else "N/A"
                print(
                    f"  {status_icon} {d.delivery_id[:12]}...  {d.event:25s}  {d.status:10s}  {timestamp}"
                )
                if d.status == "failed" and d.error_message:
                    print(f"    Error: {d.error_message[:60]}...")
                if d.response_code:
                    print(f"    Response: HTTP {d.response_code}")

    return 0
