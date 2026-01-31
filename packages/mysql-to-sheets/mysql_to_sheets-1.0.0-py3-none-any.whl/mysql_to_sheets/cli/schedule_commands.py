"""CLI commands for schedule management.

Contains: schedule add/list/remove/enable/disable/trigger/run commands.

NOTE: Schedule commands require PRO tier or higher. The tier check is performed
at the command dispatch level to provide consistent enforcement.
"""

from __future__ import annotations

import argparse
import json
import signal
import time
from typing import Any

from mysql_to_sheets.cli.tier_check import require_cli_tier
from mysql_to_sheets.cli.utils import output_result
from mysql_to_sheets.core.exceptions import SchedulerError
from mysql_to_sheets.core.scheduler import ScheduledJob, get_scheduler_service


def add_schedule_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add schedule management command parsers.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    schedule_parser = subparsers.add_parser(
        "schedule",
        help="Manage scheduled sync jobs",
    )
    schedule_subparsers = schedule_parser.add_subparsers(
        dest="schedule_command",
        help="Schedule commands",
    )

    # schedule add
    schedule_add = schedule_subparsers.add_parser(
        "add",
        help="Add a new scheduled job",
    )
    schedule_add.add_argument(
        "--name",
        required=True,
        help="Name for the scheduled job",
    )
    schedule_add.add_argument(
        "--cron",
        help="Cron expression (e.g., '0 6 * * *' for daily at 6 AM)",
    )
    schedule_add.add_argument(
        "--interval",
        type=int,
        help="Interval in minutes (alternative to cron)",
    )
    schedule_add.add_argument(
        "--sheet-id",
        help="Override Google Sheet ID",
    )
    schedule_add.add_argument(
        "--worksheet",
        help="Override worksheet name",
    )
    schedule_add.add_argument(
        "--query",
        help="Override SQL query",
    )
    schedule_add.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # schedule list
    schedule_list = schedule_subparsers.add_parser(
        "list",
        help="List all scheduled jobs",
    )
    schedule_list.add_argument(
        "--include-disabled",
        action="store_true",
        help="Include disabled jobs",
    )
    schedule_list.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # schedule remove
    schedule_remove = schedule_subparsers.add_parser(
        "remove",
        help="Remove a scheduled job",
    )
    schedule_remove.add_argument(
        "--id",
        type=int,
        required=True,
        help="ID of the job to remove",
    )
    schedule_remove.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # schedule enable
    schedule_enable = schedule_subparsers.add_parser(
        "enable",
        help="Enable a disabled scheduled job",
    )
    schedule_enable.add_argument(
        "--id",
        type=int,
        required=True,
        help="ID of the job to enable",
    )
    schedule_enable.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # schedule disable
    schedule_disable = schedule_subparsers.add_parser(
        "disable",
        help="Disable a scheduled job",
    )
    schedule_disable.add_argument(
        "--id",
        type=int,
        required=True,
        help="ID of the job to disable",
    )
    schedule_disable.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # schedule trigger
    schedule_trigger = schedule_subparsers.add_parser(
        "trigger",
        help="Trigger a scheduled job to run immediately",
    )
    schedule_trigger.add_argument(
        "--id",
        type=int,
        required=True,
        help="ID of the job to trigger",
    )
    schedule_trigger.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # schedule run
    schedule_run = schedule_subparsers.add_parser(
        "run",
        help="Start the scheduler daemon",
    )
    schedule_run.add_argument(
        "--foreground",
        action="store_true",
        help="Run in foreground (don't daemonize)",
    )
    schedule_run.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging",
    )


@require_cli_tier("scheduler")
def cmd_schedule(args: argparse.Namespace) -> int:
    """Execute schedule command.

    Requires PRO tier or higher license.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    if args.schedule_command == "add":
        return cmd_schedule_add(args)
    elif args.schedule_command == "list":
        return cmd_schedule_list(args)
    elif args.schedule_command == "remove":
        return cmd_schedule_remove(args)
    elif args.schedule_command == "enable":
        return cmd_schedule_enable(args)
    elif args.schedule_command == "disable":
        return cmd_schedule_disable(args)
    elif args.schedule_command == "trigger":
        return cmd_schedule_trigger(args)
    elif args.schedule_command == "run":
        return cmd_schedule_run(args)
    else:
        print("Error: No schedule command specified. Use --help for usage.")
        return 1


def cmd_schedule_add(args: argparse.Namespace) -> int:
    """Execute schedule add command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Validate schedule parameters
    if not args.cron and not args.interval:
        output_result(
            {
                "success": False,
                "message": "Either --cron or --interval is required",
            },
            args.output,
        )
        return 1

    # Mutual exclusivity: cannot provide both cron and interval
    if args.cron and args.interval:
        output_result(
            {
                "success": False,
                "message": "Cannot specify both --cron and --interval. Choose one scheduling method.",
            },
            args.output,
        )
        return 1

    # Validate interval bounds
    if args.interval is not None and args.interval <= 0:
        output_result(
            {
                "success": False,
                "message": f"--interval must be a positive integer, got {args.interval}",
            },
            args.output,
        )
        return 1

    try:
        service = get_scheduler_service()

        job = ScheduledJob(
            name=args.name,
            cron_expression=args.cron,
            interval_minutes=args.interval,
            sheet_id=args.sheet_id,
            worksheet_name=args.worksheet,
            sql_query=args.query,
        )

        created = service.add_job(job)

        if args.output == "json":
            print(
                json.dumps(
                    {
                        "success": True,
                        "message": "Schedule created successfully",
                        "schedule": created.to_dict(),
                    },
                    indent=2,
                )
            )
        else:
            print("Schedule created successfully!")
            print()
            print(f"  ID:       {created.id}")
            print(f"  Name:     {created.name}")
            print(f"  Schedule: {created.schedule_display}")
            if created.sheet_id:
                print(f"  Sheet:    {created.sheet_id}")

        return 0

    except SchedulerError as e:
        output_result(
            {
                "success": False,
                "message": e.message,
            },
            args.output,
        )
        return 1


def cmd_schedule_list(args: argparse.Namespace) -> int:
    """Execute schedule list command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    service = get_scheduler_service()
    jobs = service.get_all_jobs(include_disabled=args.include_disabled)

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "schedules": [j.to_dict() for j in jobs],
                    "total": len(jobs),
                },
                indent=2,
            )
        )
    else:
        if not jobs:
            print("No scheduled jobs found.")
        else:
            print(f"Scheduled Jobs ({len(jobs)} found):")
            print("-" * 100)
            print(f"  {'ID':>4}  {'Name':<25}  {'Schedule':<20}  {'Status':<10}  {'Last Run'}")
            print("-" * 100)
            for job in jobs:
                status = job.status.value
                last_run = (
                    job.last_run_at.strftime("%Y-%m-%d %H:%M") if job.last_run_at else "never"
                )
                print(
                    f"  {job.id:>4}  {job.name[:25]:<25}  {job.schedule_display[:20]:<20}  {status:<10}  {last_run}"
                )

    return 0


def cmd_schedule_remove(args: argparse.Namespace) -> int:
    """Execute schedule remove command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    service = get_scheduler_service()
    deleted = service.delete_job(args.id)

    if not deleted:
        output_result(
            {
                "success": False,
                "message": f"Schedule with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    output_result(
        {
            "success": True,
            "message": f"Schedule {args.id} has been removed",
        },
        args.output,
    )
    return 0


def cmd_schedule_enable(args: argparse.Namespace) -> int:
    """Execute schedule enable command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    service = get_scheduler_service()

    try:
        service.enable_job(args.id)
        job = service.get_job(args.id)
        assert job is not None

        output_result(
            {
                "success": True,
                "message": f"Schedule '{job.name}' has been enabled",
            },
            args.output,
        )
        return 0

    except SchedulerError as e:
        output_result(
            {
                "success": False,
                "message": e.message,
            },
            args.output,
        )
        return 1


def cmd_schedule_disable(args: argparse.Namespace) -> int:
    """Execute schedule disable command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    service = get_scheduler_service()

    try:
        service.disable_job(args.id)
        job = service.get_job(args.id)
        assert job is not None

        output_result(
            {
                "success": True,
                "message": f"Schedule '{job.name}' has been disabled",
            },
            args.output,
        )
        return 0

    except SchedulerError as e:
        output_result(
            {
                "success": False,
                "message": e.message,
            },
            args.output,
        )
        return 1


def cmd_schedule_trigger(args: argparse.Namespace) -> int:
    """Execute schedule trigger command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    service = get_scheduler_service()
    job = service.get_job(args.id)

    if not job:
        output_result(
            {
                "success": False,
                "message": f"Schedule with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    try:
        service.trigger_job(args.id)

        # Refresh to get updated status
        job = service.get_job(args.id)
        assert job is not None

        if args.output == "json":
            print(
                json.dumps(
                    {
                        "success": True,
                        "message": f"Schedule '{job.name}' triggered",
                        "schedule": job.to_dict(),
                    },
                    indent=2,
                )
            )
        else:
            print(f"Schedule '{job.name}' triggered!")
            if job.last_run_success is not None:
                status = "Success" if job.last_run_success else "Failed"
                print(f"  Result: {status}")
                if job.last_run_rows is not None:
                    print(f"  Rows synced: {job.last_run_rows}")
                if job.last_run_message:
                    print(f"  Message: {job.last_run_message}")

        return 0

    except SchedulerError as e:
        output_result(
            {
                "success": False,
                "message": e.message,
            },
            args.output,
        )
        return 1


def cmd_schedule_run(args: argparse.Namespace) -> int:
    """Execute schedule run command (start scheduler daemon).

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.core.sync import setup_logging

    # Set up logging
    config = get_config()
    logger = setup_logging(config)

    service = get_scheduler_service()

    # Set up signal handlers for graceful shutdown
    shutdown_requested = False

    def signal_handler(signum: int, frame: Any) -> None:
        nonlocal shutdown_requested
        logger.info("Shutdown signal received...")
        shutdown_requested = True
        service.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start the scheduler
        service.start()
        logger.info("Scheduler started. Press Ctrl+C to stop.")

        # Keep running until shutdown
        while not shutdown_requested:
            time.sleep(1)

        logger.info("Scheduler stopped.")
        return 0

    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        return 1
