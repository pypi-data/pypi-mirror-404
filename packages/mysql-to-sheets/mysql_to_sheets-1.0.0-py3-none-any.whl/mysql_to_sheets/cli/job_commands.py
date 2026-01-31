"""CLI commands for job queue management.

Contains: jobs list/status/cancel/retry and worker start/stop commands.

NOTE: Job queue management requires BUSINESS tier or higher.
"""

from __future__ import annotations

import argparse
import json
import sys

from mysql_to_sheets.cli.tier_check import require_cli_tier
from mysql_to_sheets.cli.utils import (
    ensure_data_dir,
    format_table,
    get_organization_id,
    output_result,
)


def add_job_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add job management command parsers.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    jobs_parser = subparsers.add_parser(
        "jobs",
        help="Manage job queue",
    )
    jobs_subparsers = jobs_parser.add_subparsers(
        dest="jobs_command",
        help="Job commands",
    )

    # jobs list
    jobs_list = jobs_subparsers.add_parser(
        "list",
        help="List jobs in the queue",
    )
    jobs_list.add_argument(
        "--org-slug",
        help="Organization slug (required unless --all)",
    )
    jobs_list.add_argument(
        "--status",
        choices=["pending", "running", "completed", "failed", "cancelled", "dead_letter"],
        help="Filter by status",
    )
    jobs_list.add_argument(
        "--type",
        dest="job_type",
        choices=["sync", "export"],
        help="Filter by job type",
    )
    jobs_list.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of jobs to show (default: 20)",
    )
    jobs_list.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # jobs status
    jobs_status = jobs_subparsers.add_parser(
        "status",
        help="Get status of a specific job",
    )
    jobs_status.add_argument(
        "job_id",
        type=int,
        help="Job ID",
    )
    jobs_status.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # jobs cancel
    jobs_cancel = jobs_subparsers.add_parser(
        "cancel",
        help="Cancel a pending job",
    )
    jobs_cancel.add_argument(
        "job_id",
        type=int,
        help="Job ID",
    )
    jobs_cancel.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    jobs_cancel.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # jobs retry
    jobs_retry = jobs_subparsers.add_parser(
        "retry",
        help="Retry a failed job",
    )
    jobs_retry.add_argument(
        "job_id",
        type=int,
        help="Job ID",
    )
    jobs_retry.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    jobs_retry.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # jobs worker
    jobs_worker = jobs_subparsers.add_parser(
        "worker",
        help="Manage job worker",
    )
    worker_subparsers = jobs_worker.add_subparsers(
        dest="worker_command",
        help="Worker commands",
    )

    # jobs worker start
    worker_start = worker_subparsers.add_parser(
        "start",
        help="Start the job worker (blocking)",
    )
    worker_start.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Seconds between job polls (default: 1.0)",
    )
    worker_start.add_argument(
        "--stale-check-interval",
        type=int,
        default=60,
        help="Seconds between stale job cleanup (default: 60)",
    )

    # jobs stats
    jobs_stats = jobs_subparsers.add_parser(
        "stats",
        help="Show queue statistics",
    )
    jobs_stats.add_argument(
        "--org-slug",
        help="Organization slug (optional)",
    )
    jobs_stats.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # jobs cleanup
    jobs_cleanup = jobs_subparsers.add_parser(
        "cleanup",
        help="Clean up old jobs",
    )
    jobs_cleanup.add_argument(
        "--days",
        type=int,
        default=30,
        help="Delete jobs older than this many days (default: 30)",
    )
    jobs_cleanup.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # jobs dlq - Dead Letter Queue subcommands
    jobs_dlq = jobs_subparsers.add_parser(
        "dlq",
        help="Manage dead letter queue",
    )
    dlq_subparsers = jobs_dlq.add_subparsers(
        dest="dlq_command",
        help="DLQ commands",
    )

    # jobs dlq list
    dlq_list = dlq_subparsers.add_parser(
        "list",
        help="List jobs in dead letter queue",
    )
    dlq_list.add_argument(
        "--org-slug",
        help="Organization slug",
    )
    dlq_list.add_argument(
        "--type",
        dest="job_type",
        choices=["sync", "export"],
        help="Filter by job type",
    )
    dlq_list.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of jobs to show (default: 20)",
    )
    dlq_list.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # jobs dlq retry
    dlq_retry = dlq_subparsers.add_parser(
        "retry",
        help="Retry a job from dead letter queue",
    )
    dlq_retry.add_argument(
        "job_id",
        type=int,
        help="Job ID to retry",
    )
    dlq_retry.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    dlq_retry.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # jobs dlq purge
    dlq_purge = dlq_subparsers.add_parser(
        "purge",
        help="Purge jobs from dead letter queue",
    )
    dlq_purge.add_argument(
        "--org-slug",
        help="Organization slug (purges all orgs if not specified)",
    )
    dlq_purge.add_argument(
        "--older-than",
        type=int,
        help="Only purge jobs older than this many days",
    )
    dlq_purge.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


@require_cli_tier("job_queue")
def handle_jobs_command(args: argparse.Namespace) -> int:
    """Handle jobs commands.

    Requires BUSINESS tier or higher license.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    db_path = ensure_data_dir()

    if args.jobs_command == "list":
        return _cmd_jobs_list(args, db_path)
    elif args.jobs_command == "status":
        return _cmd_jobs_status(args, db_path)
    elif args.jobs_command == "cancel":
        return _cmd_jobs_cancel(args, db_path)
    elif args.jobs_command == "retry":
        return _cmd_jobs_retry(args, db_path)
    elif args.jobs_command == "worker":
        return _cmd_jobs_worker(args, db_path)
    elif args.jobs_command == "stats":
        return _cmd_jobs_stats(args, db_path)
    elif args.jobs_command == "cleanup":
        return _cmd_jobs_cleanup(args, db_path)
    elif args.jobs_command == "dlq":
        return _cmd_jobs_dlq(args, db_path)
    else:
        print("Error: Unknown jobs command. Use --help for usage.", file=sys.stderr)
        return 1


def _cmd_jobs_list(args: argparse.Namespace, db_path: str) -> int:
    """List jobs in the queue."""
    from mysql_to_sheets.core.job_queue import list_jobs

    # Get organization ID if provided
    org_id = None
    if args.org_slug:
        org_id = get_organization_id(args.org_slug, db_path)
        if not org_id:
            output_result(
                {"success": False, "message": f"Organization not found: {args.org_slug}"},
                args.output,
            )
            return 1
    else:
        # List from first org or show error
        from mysql_to_sheets.models.organizations import OrganizationRepository

        org_repo = OrganizationRepository(db_path)
        orgs = org_repo.get_all()
        if orgs:
            org_id = orgs[0].id
        else:
            output_result(
                {"success": False, "message": "No organizations found. Create one first."},
                args.output,
            )
            return 1

    assert org_id is not None
    jobs = list_jobs(
        organization_id=org_id,
        status=args.status,
        job_type=args.job_type,
        limit=args.limit,
        db_path=db_path,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "jobs": [j.to_dict() for j in jobs],
                    "count": len(jobs),
                },
                indent=2,
                default=str,
            )
        )
    else:
        if not jobs:
            print("No jobs found.")
        else:
            headers = ["ID", "Type", "Status", "Priority", "Attempts", "Created"]
            rows = [
                [
                    j.id,
                    j.job_type,
                    j.status,
                    j.priority,
                    f"{j.attempts}/{j.max_attempts}",
                    j.created_at.strftime("%Y-%m-%d %H:%M") if j.created_at else "-",
                ]
                for j in jobs
            ]
            print(format_table(headers, rows))
            print(f"\nTotal: {len(jobs)} jobs")

    return 0


def _cmd_jobs_status(args: argparse.Namespace, db_path: str) -> int:
    """Get status of a specific job."""
    from mysql_to_sheets.core.job_queue import get_job_status

    job = get_job_status(args.job_id, db_path=db_path)

    if not job:
        output_result(
            {"success": False, "message": f"Job not found: {args.job_id}"},
            args.output,
        )
        return 1

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "job": job.to_dict(),
                },
                indent=2,
                default=str,
            )
        )
    else:
        print(f"Job ID: {job.id}")
        print(f"Type: {job.job_type}")
        print(f"Status: {job.status}")
        print(f"Priority: {job.priority}")
        print(f"Attempts: {job.attempts}/{job.max_attempts}")
        print(f"Created: {job.created_at}")
        if job.started_at:
            print(f"Started: {job.started_at}")
        if job.completed_at:
            print(f"Completed: {job.completed_at}")
        if job.error:
            print(f"Error: {job.error}")
        if job.result:
            print(f"Result: {json.dumps(job.result, indent=2)}")

    return 0


def _cmd_jobs_cancel(args: argparse.Namespace, db_path: str) -> int:
    """Cancel a pending job."""
    from mysql_to_sheets.core.job_queue import cancel_job

    org_id = get_organization_id(args.org_slug, db_path)
    if not org_id:
        output_result(
            {"success": False, "message": f"Organization not found: {args.org_slug}"},
            args.output,
        )
        return 1

    success = cancel_job(args.job_id, org_id, db_path=db_path)

    if success:
        output_result(
            {"success": True, "message": f"Job {args.job_id} cancelled"},
            args.output,
        )
        return 0
    else:
        output_result(
            {
                "success": False,
                "message": f"Failed to cancel job {args.job_id} (not found or not pending)",
            },
            args.output,
        )
        return 1


def _cmd_jobs_retry(args: argparse.Namespace, db_path: str) -> int:
    """Retry a failed job."""
    from mysql_to_sheets.core.job_queue import retry_job

    org_id = get_organization_id(args.org_slug, db_path)
    if not org_id:
        output_result(
            {"success": False, "message": f"Organization not found: {args.org_slug}"},
            args.output,
        )
        return 1

    job = retry_job(args.job_id, org_id, db_path=db_path)

    if job:
        output_result(
            {"success": True, "message": f"Job {args.job_id} requeued for retry"},
            args.output,
        )
        return 0
    else:
        output_result(
            {
                "success": False,
                "message": f"Failed to retry job {args.job_id} (not found or not failed)",
            },
            args.output,
        )
        return 1


def _cmd_jobs_worker(args: argparse.Namespace, db_path: str) -> int:
    """Handle worker subcommands."""
    if args.worker_command == "start":
        from mysql_to_sheets.core.job_worker import run_worker

        print(f"Starting job worker (poll_interval={args.poll_interval}s)")
        print("Press Ctrl+C to stop")

        run_worker(
            db_path=db_path,
            poll_interval=args.poll_interval,
            stale_check_interval=args.stale_check_interval,
        )
        return 0
    else:
        print("Error: Unknown worker command. Use --help for usage.", file=sys.stderr)
        return 1


def _cmd_jobs_stats(args: argparse.Namespace, db_path: str) -> int:
    """Show queue statistics."""
    from mysql_to_sheets.core.job_queue import count_dead_letter_jobs, get_queue_stats

    org_id = None
    if args.org_slug:
        org_id = get_organization_id(args.org_slug, db_path)
        if not org_id:
            output_result(
                {"success": False, "message": f"Organization not found: {args.org_slug}"},
                args.output,
            )
            return 1

    stats = get_queue_stats(organization_id=org_id, db_path=db_path)
    dlq_count = count_dead_letter_jobs(organization_id=org_id, db_path=db_path)
    stats["dead_letter"] = dlq_count

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "stats": stats,
                },
                indent=2,
            )
        )
    else:
        print("Job Queue Statistics:")
        print(f"  Pending:     {stats['pending']}")
        print(f"  Running:     {stats['running']}")
        print(f"  Completed:   {stats['completed']}")
        print(f"  Failed:      {stats['failed']}")
        print(f"  Cancelled:   {stats['cancelled']}")
        print(f"  Dead Letter: {dlq_count}")
        total = sum(stats.values())
        print(f"  Total:       {total}")

    return 0


def _cmd_jobs_cleanup(args: argparse.Namespace, db_path: str) -> int:
    """Clean up old jobs."""
    from mysql_to_sheets.core.job_queue import delete_old_jobs

    deleted = delete_old_jobs(days=args.days, db_path=db_path)

    output_result(
        {"success": True, "message": f"Deleted {deleted} jobs older than {args.days} days"},
        args.output,
    )
    return 0


def _cmd_jobs_dlq(args: argparse.Namespace, db_path: str) -> int:
    """Handle DLQ subcommands."""
    if args.dlq_command == "list":
        return _cmd_dlq_list(args, db_path)
    elif args.dlq_command == "retry":
        return _cmd_dlq_retry(args, db_path)
    elif args.dlq_command == "purge":
        return _cmd_dlq_purge(args, db_path)
    else:
        print("Error: Unknown DLQ command. Use --help for usage.", file=sys.stderr)
        return 1


def _cmd_dlq_list(args: argparse.Namespace, db_path: str) -> int:
    """List jobs in dead letter queue."""
    from mysql_to_sheets.core.job_queue import list_dead_letter_jobs

    # Get organization ID if provided
    org_id = None
    if args.org_slug:
        org_id = get_organization_id(args.org_slug, db_path)
        if not org_id:
            output_result(
                {"success": False, "message": f"Organization not found: {args.org_slug}"},
                args.output,
            )
            return 1

    jobs = list_dead_letter_jobs(
        organization_id=org_id,
        job_type=args.job_type,
        limit=args.limit,
        db_path=db_path,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "jobs": [j.to_dict() for j in jobs],
                    "count": len(jobs),
                },
                indent=2,
                default=str,
            )
        )
    else:
        if not jobs:
            print("No jobs in dead letter queue.")
        else:
            headers = ["ID", "Type", "Priority", "Attempts", "Error", "Completed"]
            rows = [
                [
                    j.id,
                    j.job_type,
                    j.priority,
                    f"{j.attempts}/{j.max_attempts}",
                    (j.error[:40] + "...") if j.error and len(j.error) > 40 else j.error or "-",
                    j.completed_at.strftime("%Y-%m-%d %H:%M") if j.completed_at else "-",
                ]
                for j in jobs
            ]
            print(format_table(headers, rows))
            print(f"\nTotal: {len(jobs)} dead letter jobs")

    return 0


def _cmd_dlq_retry(args: argparse.Namespace, db_path: str) -> int:
    """Retry a job from dead letter queue."""
    from mysql_to_sheets.core.job_queue import retry_dead_letter_job

    org_id = get_organization_id(args.org_slug, db_path)
    if not org_id:
        output_result(
            {"success": False, "message": f"Organization not found: {args.org_slug}"},
            args.output,
        )
        return 1

    job = retry_dead_letter_job(args.job_id, org_id, db_path=db_path)

    if job:
        output_result(
            {"success": True, "message": f"Dead letter job {args.job_id} requeued for retry"},
            args.output,
        )
        return 0
    else:
        output_result(
            {
                "success": False,
                "message": f"Failed to retry job {args.job_id} (not found or not in dead_letter status)",
            },
            args.output,
        )
        return 1


def _cmd_dlq_purge(args: argparse.Namespace, db_path: str) -> int:
    """Purge jobs from dead letter queue."""
    from mysql_to_sheets.core.job_queue import purge_dead_letter_queue

    org_id = None
    if args.org_slug:
        org_id = get_organization_id(args.org_slug, db_path)
        if not org_id:
            output_result(
                {"success": False, "message": f"Organization not found: {args.org_slug}"},
                args.output,
            )
            return 1

    purged = purge_dead_letter_queue(
        organization_id=org_id,
        older_than_days=args.older_than,
        db_path=db_path,
    )

    message = f"Purged {purged} dead letter job(s)"
    if args.older_than:
        message += f" older than {args.older_than} days"

    output_result(
        {"success": True, "message": message, "purged_count": purged},
        args.output,
    )
    return 0
