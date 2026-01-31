"""Built-in scheduler for automated sync operations.

This module provides a native scheduling capability that allows users
to schedule sync operations without external tools like cron. It supports
cron expressions and interval-based scheduling.
"""

from mysql_to_sheets.core.scheduler.models import JobStatus, ScheduledJob
from mysql_to_sheets.core.scheduler.repository import (
    ScheduleRepository,
    SQLiteScheduleRepository,
    get_schedule_repository,
    reset_schedule_repository,
)
from mysql_to_sheets.core.scheduler.service import (
    SchedulerService,
    get_scheduler_service,
    reset_scheduler_service,
)

__all__ = [
    # Models
    "ScheduledJob",
    "JobStatus",
    # Repository
    "ScheduleRepository",
    "SQLiteScheduleRepository",
    "get_schedule_repository",
    "reset_schedule_repository",
    # Service
    "SchedulerService",
    "get_scheduler_service",
    "reset_scheduler_service",
]
