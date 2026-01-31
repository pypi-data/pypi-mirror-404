"""Entry point for the Hybrid Agent.

Usage:
    python -m mysql_to_sheets.agent run
    python -m mysql_to_sheets.agent status
    python -m mysql_to_sheets.agent health
    python -m mysql_to_sheets.agent version
"""

import argparse
import json
import logging
import os
import sys
from typing import NoReturn

from mysql_to_sheets import __version__


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for agent mode."""
    level = logging.DEBUG if verbose else logging.INFO
    log_format = os.getenv(
        "AGENT_LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reduce noise from urllib3
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def cmd_run(args: argparse.Namespace) -> int:
    """Run the agent worker."""
    from mysql_to_sheets.agent import run_agent

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Validate required environment
    if not os.getenv("LINK_TOKEN"):
        logger.error("LINK_TOKEN environment variable is required")
        return 1

    logger.info(f"Starting MySQL to Sheets Agent v{__version__}")
    logger.info(f"Control plane: {args.control_plane_url or os.getenv('CONTROL_PLANE_URL', 'https://app.mysql-to-sheets.com')}")

    try:
        run_agent(
            control_plane_url=args.control_plane_url,
            agent_id=args.agent_id,
            poll_interval=args.poll_interval,
            heartbeat_interval=args.heartbeat_interval,
        )
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.exception(f"Agent error: {e}")
        return 1

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Check agent token status."""
    from mysql_to_sheets.agent.link_token import get_link_token_info

    setup_logging(args.verbose)

    token_info = get_link_token_info()

    if args.output == "json":
        print(json.dumps(token_info.to_dict(), indent=2))
    else:
        print(f"Status: {token_info.status.value}")
        if token_info.organization_id:
            print(f"Organization: {token_info.organization_id}")
        if token_info.permissions:
            print(f"Permissions: {', '.join(token_info.permissions)}")
        if token_info.issued_at:
            print(f"Issued at: {token_info.issued_at}")
        if token_info.error:
            print(f"Error: {token_info.error}")

    return 0 if token_info.status.value == "valid" else 1


def cmd_health(args: argparse.Namespace) -> int:
    """Health check for container orchestration."""
    import json as json_module
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    # Check token
    from mysql_to_sheets.agent.link_token import get_link_token_info

    token_info = get_link_token_info()
    if token_info.status.value != "valid":
        if args.output == "json":
            print(json_module.dumps({"healthy": False, "error": "Invalid token"}))
        else:
            print("UNHEALTHY: Invalid token")
        return 1

    # Check control plane connectivity
    control_plane_url = (
        args.control_plane_url
        or os.getenv("CONTROL_PLANE_URL", "https://app.mysql-to-sheets.com")
    ).rstrip("/")

    try:
        link_token = os.getenv("LINK_TOKEN", "")
        request = Request(
            f"{control_plane_url}/api/agent/health",
            headers={
                "Authorization": f"Bearer {link_token}",
                "Accept": "application/json",
            },
        )
        response = urlopen(request, timeout=10)
        data = json_module.loads(response.read().decode("utf-8"))

        if args.output == "json":
            print(json_module.dumps({"healthy": True, "control_plane": data}))
        else:
            print("HEALTHY")
        return 0

    except (HTTPError, URLError) as e:
        if args.output == "json":
            print(json_module.dumps({"healthy": False, "error": str(e)}))
        else:
            print(f"UNHEALTHY: Cannot reach control plane - {e}")
        return 1


def cmd_version(args: argparse.Namespace) -> int:
    """Show version information."""
    from mysql_to_sheets.agent.updater import get_agent_update_checker

    if args.output == "json":
        info = {
            "version": __version__,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }

        # Check for updates if requested
        if args.check_updates:
            checker = get_agent_update_checker()
            update = checker.check_for_updates(force=True)
            if update:
                info["update_available"] = update.to_dict()

        print(json.dumps(info, indent=2))
    else:
        print(f"MySQL to Sheets Agent v{__version__}")
        print(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

        if args.check_updates:
            checker = get_agent_update_checker()
            update = checker.check_for_updates(force=True)
            if update:
                print(f"\nUpdate available: v{update.version}")
                print(f"Download: {update.release_url}")

    return 0


def cmd_test_sync(args: argparse.Namespace) -> int:
    """Test sync without actually pushing data."""
    from mysql_to_sheets.agent.link_config_provider import LinkConfigProvider
    from mysql_to_sheets.core.sync import run_sync

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("Running test sync (dry-run mode)")

    try:
        # Get config from control plane
        provider = LinkConfigProvider(
            control_plane_url=args.control_plane_url,
            config_name=args.config_name,
        )
        config = provider.get_config()

        # Run sync in dry-run mode
        result = run_sync(config=config, dry_run=True)

        if args.output == "json":
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"Test sync {'succeeded' if result.success else 'failed'}")
            if result.success:
                print(f"Would sync {result.rows_synced} rows")
                print(f"Columns: {', '.join(result.headers)}")
            else:
                print(f"Error: {result.error}")

        return 0 if result.success else 1

    except Exception as e:
        logger.exception(f"Test sync failed: {e}")
        if args.output == "json":
            print(json.dumps({"success": False, "error": str(e)}, indent=2))
        return 1


def main() -> NoReturn:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="mysql-to-sheets-agent",
        description="Hybrid Agent for MySQL to Sheets Sync",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Run the agent worker")
    run_parser.add_argument(
        "--control-plane-url",
        help="Control plane URL (default: CONTROL_PLANE_URL env var)",
    )
    run_parser.add_argument(
        "--agent-id",
        help="Agent ID (default: auto-generated)",
    )
    run_parser.add_argument(
        "--poll-interval",
        type=float,
        default=5.0,
        help="Seconds between job polls (default: 5.0)",
    )
    run_parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=30,
        help="Seconds between heartbeats (default: 30)",
    )
    run_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    run_parser.set_defaults(func=cmd_run)

    # status command
    status_parser = subparsers.add_parser("status", help="Check token status")
    status_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    status_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    status_parser.set_defaults(func=cmd_status)

    # health command
    health_parser = subparsers.add_parser("health", help="Health check for containers")
    health_parser.add_argument(
        "--control-plane-url",
        help="Control plane URL",
    )
    health_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    health_parser.set_defaults(func=cmd_health)

    # version command
    version_parser = subparsers.add_parser("version", help="Show version info")
    version_parser.add_argument(
        "--check-updates",
        action="store_true",
        help="Check for available updates",
    )
    version_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    version_parser.set_defaults(func=cmd_version)

    # test-sync command
    test_parser = subparsers.add_parser("test-sync", help="Test sync (dry-run)")
    test_parser.add_argument(
        "--control-plane-url",
        help="Control plane URL",
    )
    test_parser.add_argument(
        "--config-name",
        help="Sync config name to test",
    )
    test_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    test_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    test_parser.set_defaults(func=cmd_test_sync)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
