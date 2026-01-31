"""CLI commands for license management.

Contains: license status command to display license information.
"""

from __future__ import annotations

import argparse
from typing import Any

from mysql_to_sheets.cli.output import error, info, success, warning
from mysql_to_sheets.cli.utils import output_result
from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.license import (
    LicenseInfo,
    LicenseStatus,
    validate_license,
)


def add_license_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add license-related command parsers.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    license_parser = subparsers.add_parser(
        "license",
        help="License management commands",
    )
    license_subparsers = license_parser.add_subparsers(
        dest="license_command",
        help="License commands",
    )

    # license status
    status_parser = license_subparsers.add_parser(
        "status",
        help="Show license status and details",
    )
    status_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # license info (alias for status)
    info_parser = license_subparsers.add_parser(
        "info",
        help="Show license information (alias for status)",
    )
    info_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def _format_license_status(license_info: LicenseInfo, output_format: str) -> dict[str, Any]:
    """Format license information for output.

    Args:
        license_info: Validated license information.
        output_format: Output format ('text' or 'json').

    Returns:
        Dictionary with formatted license data.
    """
    data = {
        "status": license_info.status.value,
        "tier": license_info.tier.value,
        "customer_id": license_info.customer_id,
        "email": license_info.email,
        "issued_at": (
            license_info.issued_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if license_info.issued_at
            else None
        ),
        "expires_at": (
            license_info.expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if license_info.expires_at
            else None
        ),
        "days_until_expiry": license_info.days_until_expiry,
        "features": license_info.features,
        "error": license_info.error,
    }

    # Add validity flag
    data["valid"] = license_info.status in (
        LicenseStatus.VALID,
        LicenseStatus.GRACE_PERIOD,
    )

    return data


def cmd_license_status(args: argparse.Namespace) -> int:
    """Show license status and details.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for valid license, 1 for invalid/missing).
    """
    config = get_config()

    # Check if license is configured
    if not config.license_key:
        if args.output == "json":
            output_result(
                {
                    "status": "missing",
                    "valid": False,
                    "tier": "free",
                    "message": "No license key configured",
                },
                args.output,
            )
        else:
            print(warning("No license key configured"))
            print(info("Set LICENSE_KEY in your .env file to unlock premium features"))
            print(info("Running in FREE tier with limited functionality"))
            print()
            print(info("To purchase a license, visit: https://example.com/pricing"))
        return 1

    # Validate the license
    license_info = validate_license(
        config.license_key,
        config.license_public_key or None,
        config.license_offline_grace_days,
    )

    data = _format_license_status(license_info, args.output)

    if args.output == "json":
        output_result(data, args.output)
    else:
        # Text output
        _print_license_text(license_info, config)

    # Return success for valid/grace period, failure otherwise
    return 0 if data["valid"] else 1


def _print_license_text(license_info: LicenseInfo, config: Any) -> None:
    """Print license information in text format.

    Args:
        license_info: Validated license information.
        config: Application configuration.
    """
    print()
    print("License Information")
    print("=" * 40)

    # Status with color coding
    status = license_info.status
    if status == LicenseStatus.VALID:
        print(success(f"Status: {status.value.upper()}"))
    elif status == LicenseStatus.GRACE_PERIOD:
        print(warning(f"Status: {status.value.upper()} (License expired but in grace period)"))
    elif status == LicenseStatus.EXPIRED:
        print(error(f"Status: {status.value.upper()}"))
    elif status == LicenseStatus.INVALID:
        print(error(f"Status: {status.value.upper()}"))
    elif status == LicenseStatus.MISSING:
        print(warning(f"Status: {status.value.upper()}"))

    # Tier
    tier_str = license_info.tier.value.upper()
    print(f"Tier: {tier_str}")

    # Customer info
    if license_info.email:
        print(f"Licensed to: {license_info.email}")
    if license_info.customer_id:
        print(f"Customer ID: {license_info.customer_id}")

    # Dates
    if license_info.issued_at:
        print(f"Issued: {license_info.issued_at.strftime('%Y-%m-%d')}")
    if license_info.expires_at:
        print(f"Expires: {license_info.expires_at.strftime('%Y-%m-%d')}")

    # Days remaining
    if license_info.days_until_expiry is not None:
        days = license_info.days_until_expiry
        if days > 0:
            if days <= 7:
                print(warning(f"Days remaining: {days} (expiring soon!)"))
            else:
                print(f"Days remaining: {days}")
        elif days == 0:
            print(warning("Days remaining: Expires today!"))
        else:
            print(error(f"Expired: {-days} days ago"))

    # Features
    if license_info.features:
        print(f"Features: {', '.join(license_info.features)}")

    # Error message
    if license_info.error:
        print()
        print(error(f"Error: {license_info.error}"))

    # Hints based on status
    print()
    if status == LicenseStatus.VALID:
        print(info(f"Your {tier_str} license is active"))
    elif status == LicenseStatus.GRACE_PERIOD:
        print(warning("Please renew your license to continue using premium features"))
        if config.billing_portal_url:
            print(info(f"Renew at: {config.billing_portal_url}"))
    elif status == LicenseStatus.EXPIRED:
        print(error("Your license has expired"))
        print(info("Renew your subscription to restore premium features"))
        if config.billing_portal_url:
            print(info(f"Renew at: {config.billing_portal_url}"))
    elif status == LicenseStatus.INVALID:
        print(error("Your license key is invalid"))
        print(info("Please check that LICENSE_KEY is correct in your .env file"))
        print(info("Contact support if you believe this is an error"))

    print()


def handle_license_command(args: argparse.Namespace) -> int:
    """Handle license subcommands.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    if args.license_command in ("status", "info"):
        return cmd_license_status(args)
    elif args.license_command is None:
        # Show status by default if no subcommand
        args.output = "text"
        return cmd_license_status(args)
    else:
        error(f"Unknown license command: {args.license_command}")
        return 1
