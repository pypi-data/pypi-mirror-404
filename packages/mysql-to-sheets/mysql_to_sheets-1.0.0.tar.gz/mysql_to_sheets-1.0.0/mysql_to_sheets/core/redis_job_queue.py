"""Redis-based job queue backend.

Provides a Redis implementation of the JobQueueBackend interface,
enabling distributed job processing across multiple workers.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from mysql_to_sheets.core.job_backend import JobQueueBackend
from mysql_to_sheets.core.logging_utils import get_module_logger
from mysql_to_sheets.models.jobs import VALID_JOB_STATUSES, Job
from mysql_to_sheets.models.utils import parse_datetime, parse_int

logger = get_module_logger(__name__)

# Redis key prefixes
KEY_COUNTER = "jobs:counter"
KEY_PENDING = "jobs:pending"  # Sorted set: score = -priority * 1e12 + timestamp
KEY_DATA = "jobs:data"  # Hash prefix: jobs:data:{id}
KEY_ORG = "jobs:org"  # Set prefix: jobs:org:{org_id}
KEY_STATUS = "jobs:status"  # Set prefix: jobs:status:{status}


class RedisJobQueue(JobQueueBackend):
    """Redis-based job queue backend.

    Uses Redis data structures for distributed job processing:
    - `jobs:counter`: Auto-increment ID counter
    - `jobs:pending`: Sorted set of pending job IDs (score = priority/time)
    - `jobs:data:{id}`: Hash containing job fields
    - `jobs:org:{org_id}`: Set of job IDs per organization
    - `jobs:status:{status}`: Set of job IDs per status

    Attributes:
        redis: Redis client instance.
        ttl_seconds: TTL for completed job data.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = 86400,
        redis_client: Any = None,
    ) -> None:
        """Initialize Redis job queue.

        Args:
            redis_url: Redis connection URL.
            ttl_seconds: TTL for completed job data (default: 24 hours).
            redis_client: Optional pre-configured Redis client (for testing).
        """
        self._ttl_seconds = ttl_seconds

        if redis_client is not None:
            self._redis = redis_client
        else:
            try:
                import redis

                self._redis = redis.from_url(redis_url, decode_responses=True)
            except ImportError:
                raise ImportError(
                    "redis package is required for RedisJobQueue. "
                    "Install with: pip install redis>=5.0.0"
                )

    @property
    def redis(self) -> Any:
        """Get the Redis client."""
        return self._redis

    def _job_key(self, job_id: int) -> str:
        """Get the Redis key for a job's data hash."""
        return f"{KEY_DATA}:{job_id}"

    def _org_key(self, org_id: int) -> str:
        """Get the Redis key for an organization's job set."""
        return f"{KEY_ORG}:{org_id}"

    def _status_key(self, status: str) -> str:
        """Get the Redis key for a status set."""
        return f"{KEY_STATUS}:{status}"

    def _score_for_job(self, priority: int, created_at: datetime | None = None) -> float:
        """Calculate the score for sorting in the pending queue.

        Higher priority jobs have lower scores (sorted first).
        Within same priority, older jobs have lower scores.

        Args:
            priority: Job priority (higher = more important).
            created_at: Job creation timestamp.

        Returns:
            Score for sorted set.
        """
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        # Use negative priority so higher priority sorts first
        # Add timestamp so older jobs within same priority sort first
        timestamp = created_at.timestamp()
        return -priority * 1e12 + timestamp

    def _job_to_hash(self, job: Job) -> dict[str, str]:
        """Convert a Job to a Redis hash (string values)."""
        return {
            "id": str(job.id) if job.id else "",
            "organization_id": str(job.organization_id),
            "user_id": str(job.user_id) if job.user_id else "",
            "job_type": job.job_type,
            "status": job.status,
            "priority": str(job.priority),
            "payload": json.dumps(job.payload),
            "result": json.dumps(job.result) if job.result else "",
            "error": job.error or "",
            "created_at": job.created_at.isoformat() if job.created_at else "",
            "started_at": job.started_at.isoformat() if job.started_at else "",
            "completed_at": job.completed_at.isoformat() if job.completed_at else "",
            "attempts": str(job.attempts),
            "max_attempts": str(job.max_attempts),
            "worker_id": getattr(job, "worker_id", "") or "",
            "heartbeat_at": str(getattr(job, "heartbeat_at", None) or ""),
        }

    def _hash_to_job(self, data: dict[str, str]) -> Job | None:
        """Convert a Redis hash to a Job dataclass."""
        if not data:
            return None

        def parse_json(value: str, field_name: str = "unknown") -> dict[Any, Any] | None:
            if not value:
                return None
            try:
                return json.loads(value)  # type: ignore[no-any-return]
            except json.JSONDecodeError as e:
                # Edge Case 28: Log warning instead of silently returning None
                # This makes corrupted job data visible in logs
                logger.warning(
                    "Failed to parse JSON for field '%s' (job_id=%s): %s. "
                    "Job will use empty dict for payload. Raw value: %.100s...",
                    field_name,
                    data.get("id", "?"),
                    e,
                    value,
                )
                return None

        job = Job(
            id=parse_int(data.get("id", ""), 0) or None,
            organization_id=parse_int(data.get("organization_id", ""), 0),
            user_id=parse_int(data.get("user_id", ""), 0) or None,
            job_type=data.get("job_type", "sync"),
            status=data.get("status", "pending"),
            priority=parse_int(data.get("priority", ""), 0),
            payload=parse_json(data.get("payload", ""), "payload") or {},
            result=parse_json(data.get("result", ""), "result"),
            error=data.get("error") or None,
            created_at=parse_datetime(data.get("created_at", "")),
            started_at=parse_datetime(data.get("started_at", "")),
            completed_at=parse_datetime(data.get("completed_at", "")),
            attempts=parse_int(data.get("attempts", ""), 0),
            max_attempts=parse_int(data.get("max_attempts", ""), 3),
        )

        # Add worker fields as attributes (not in base dataclass)
        job.worker_id = data.get("worker_id") or None
        job.heartbeat_at = parse_datetime(data.get("heartbeat_at", ""))

        return job

    def create(self, job: Job) -> Job:
        """Create a new job in Redis."""
        # Validate job
        errors = job.validate()
        if errors:
            raise ValueError(f"Invalid job: {', '.join(errors)}")

        # Generate ID
        job_id = self._redis.incr(KEY_COUNTER)
        job.id = job_id
        job.created_at = job.created_at or datetime.now(timezone.utc)

        # Store job data
        job_key = self._job_key(job_id)
        self._redis.hset(job_key, mapping=self._job_to_hash(job))

        # Add to organization set
        self._redis.sadd(self._org_key(job.organization_id), job_id)

        # Add to status set
        self._redis.sadd(self._status_key(job.status), job_id)

        # Add to pending queue if pending
        if job.status == "pending":
            score = self._score_for_job(job.priority, job.created_at)
            self._redis.zadd(KEY_PENDING, {str(job_id): score})

        logger.debug(f"Created job {job_id} in Redis")
        return job

    def get_by_id(
        self,
        job_id: int,
        organization_id: int | None = None,
    ) -> Job | None:
        """Get a job by ID."""
        data = self._redis.hgetall(self._job_key(job_id))
        if not data:
            return None

        job = self._hash_to_job(data)
        if job and organization_id is not None:
            if job.organization_id != organization_id:
                return None

        return job

    def get_next_pending(self, worker_id: str | None = None) -> Job | None:
        """Get and claim the next pending job atomically."""
        # Use WATCH/MULTI/EXEC for atomic claim
        pipe = self._redis.pipeline(True)

        try:
            while True:
                # Get the highest priority pending job
                result = self._redis.zrange(KEY_PENDING, 0, 0)
                if not result:
                    return None

                job_id = int(result[0])
                job_key = self._job_key(job_id)

                # Watch for changes
                pipe.watch(job_key, KEY_PENDING)

                # Verify job is still pending
                status = self._redis.hget(job_key, "status")
                if status != "pending":
                    pipe.unwatch()
                    continue

                # Get current attempts
                attempts = int(self._redis.hget(job_key, "attempts") or "0")

                # Atomic update
                pipe.multi()
                pipe.zrem(KEY_PENDING, str(job_id))
                pipe.srem(self._status_key("pending"), job_id)
                pipe.sadd(self._status_key("running"), job_id)
                pipe.hset(
                    job_key,
                    mapping={
                        "status": "running",
                        "started_at": datetime.now(timezone.utc).isoformat(),
                        "attempts": str(attempts + 1),
                        "worker_id": worker_id or "",
                        "heartbeat_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                pipe.execute()

                # Return the claimed job
                return self.get_by_id(job_id)

        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error claiming job: {e}")
            pipe.reset()
            return None

    def claim_job(self, job_id: int, worker_id: str | None = None) -> Job | None:
        """Attempt to claim a specific pending job."""
        job_key = self._job_key(job_id)

        # Check if job exists and is pending
        status = self._redis.hget(job_key, "status")
        if status != "pending":
            return None

        pipe = self._redis.pipeline(True)
        try:
            pipe.watch(job_key)

            # Re-check status
            status = self._redis.hget(job_key, "status")
            if status != "pending":
                pipe.unwatch()
                return None

            attempts = int(self._redis.hget(job_key, "attempts") or "0")

            pipe.multi()
            pipe.zrem(KEY_PENDING, str(job_id))
            pipe.srem(self._status_key("pending"), job_id)
            pipe.sadd(self._status_key("running"), job_id)
            pipe.hset(
                job_key,
                mapping={
                    "status": "running",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "attempts": str(attempts + 1),
                    "worker_id": worker_id or "",
                    "heartbeat_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            pipe.execute()

            return self.get_by_id(job_id)

        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error claiming job {job_id}: {e}")
            pipe.reset()
            return None

    def complete(self, job_id: int, result: dict[str, Any]) -> bool:
        """Mark a job as completed."""
        job_key = self._job_key(job_id)

        status = self._redis.hget(job_key, "status")
        if status != "running":
            return False

        pipe = self._redis.pipeline()
        pipe.srem(self._status_key("running"), job_id)
        pipe.sadd(self._status_key("completed"), job_id)
        pipe.hset(
            job_key,
            mapping={
                "status": "completed",
                "result": json.dumps(result),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        # Set TTL for completed jobs
        pipe.expire(job_key, self._ttl_seconds)
        pipe.execute()

        logger.debug(f"Completed job {job_id}")
        return True

    def fail(self, job_id: int, error: str, requeue: bool = True) -> bool:
        """Mark a job as failed."""
        job_key = self._job_key(job_id)

        status = self._redis.hget(job_key, "status")
        if status != "running":
            return False

        attempts = int(self._redis.hget(job_key, "attempts") or "0")
        max_attempts = int(self._redis.hget(job_key, "max_attempts") or "3")
        priority = int(self._redis.hget(job_key, "priority") or "0")
        created_at_str = self._redis.hget(job_key, "created_at")
        created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now(timezone.utc)

        pipe = self._redis.pipeline()
        pipe.srem(self._status_key("running"), job_id)

        if requeue and attempts < max_attempts:
            # Requeue job
            pipe.sadd(self._status_key("pending"), job_id)
            score = self._score_for_job(priority, created_at)
            pipe.zadd(KEY_PENDING, {str(job_id): score})
            pipe.hset(
                job_key,
                mapping={
                    "status": "pending",
                    "error": error,
                    "started_at": "",
                    "completed_at": "",
                    "worker_id": "",
                    "heartbeat_at": "",
                },
            )
        else:
            # Mark as failed permanently
            pipe.sadd(self._status_key("failed"), job_id)
            pipe.hset(
                job_key,
                mapping={
                    "status": "failed",
                    "error": error,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            pipe.expire(job_key, self._ttl_seconds)

        pipe.execute()
        logger.debug(f"Failed job {job_id}: {error}")
        return True

    def cancel(self, job_id: int, organization_id: int) -> bool:
        """Cancel a pending job."""
        job = self.get_by_id(job_id, organization_id)
        if not job or job.status != "pending":
            return False

        job_key = self._job_key(job_id)

        pipe = self._redis.pipeline()
        pipe.zrem(KEY_PENDING, str(job_id))
        pipe.srem(self._status_key("pending"), job_id)
        pipe.sadd(self._status_key("cancelled"), job_id)
        pipe.hset(
            job_key,
            mapping={
                "status": "cancelled",
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        pipe.expire(job_key, self._ttl_seconds)
        pipe.execute()

        logger.debug(f"Cancelled job {job_id}")
        return True

    def retry(self, job_id: int, organization_id: int) -> Job | None:
        """Retry a failed job."""
        job = self.get_by_id(job_id, organization_id)
        if not job or job.status != "failed":
            return None

        job_key = self._job_key(job_id)

        pipe = self._redis.pipeline()
        pipe.srem(self._status_key("failed"), job_id)
        pipe.sadd(self._status_key("pending"), job_id)
        score = self._score_for_job(job.priority, job.created_at)
        pipe.zadd(KEY_PENDING, {str(job_id): score})
        pipe.hset(
            job_key,
            mapping={
                "status": "pending",
                "error": "",
                "started_at": "",
                "completed_at": "",
                "attempts": "0",
                "worker_id": "",
                "heartbeat_at": "",
            },
        )
        # Remove TTL
        pipe.persist(job_key)
        pipe.execute()

        logger.debug(f"Retried job {job_id}")
        return self.get_by_id(job_id)

    def release_job(self, job_id: int) -> bool:
        """Release a running job back to pending state."""
        job_key = self._job_key(job_id)

        status = self._redis.hget(job_key, "status")
        if status != "running":
            return False

        priority = int(self._redis.hget(job_key, "priority") or "0")
        created_at_str = self._redis.hget(job_key, "created_at")
        created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now(timezone.utc)

        pipe = self._redis.pipeline()
        pipe.srem(self._status_key("running"), job_id)
        pipe.sadd(self._status_key("pending"), job_id)
        score = self._score_for_job(priority, created_at)
        pipe.zadd(KEY_PENDING, {str(job_id): score})
        pipe.hset(
            job_key,
            mapping={
                "status": "pending",
                "started_at": "",
                "worker_id": "",
                "heartbeat_at": "",
            },
        )
        pipe.execute()

        logger.debug(f"Released job {job_id} back to pending")
        return True

    def heartbeat(self, job_id: int, worker_id: str) -> bool:
        """Update heartbeat timestamp for a running job."""
        job_key = self._job_key(job_id)

        # Verify job is running and belongs to this worker
        pipe = self._redis.pipeline()
        pipe.hget(job_key, "status")
        pipe.hget(job_key, "worker_id")
        results = pipe.execute()

        status, current_worker = results
        if status != "running" or current_worker != worker_id:
            return False

        self._redis.hset(job_key, "heartbeat_at", datetime.now(timezone.utc).isoformat())
        return True

    def get_all(
        self,
        organization_id: int,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """Get all jobs in an organization."""
        # Get job IDs for this organization
        job_ids = self._redis.smembers(self._org_key(organization_id))
        if not job_ids:
            return []

        # Filter by status if specified
        if status:
            status_ids = self._redis.smembers(self._status_key(status))
            job_ids = job_ids & status_ids

        # Get job data
        jobs = []
        for job_id_str in job_ids:
            job = self.get_by_id(int(job_id_str))
            if job:
                # Filter by job_type if specified
                if job_type and job.job_type != job_type:
                    continue
                jobs.append(job)

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at or datetime.min, reverse=True)

        # Apply pagination
        return jobs[offset : offset + limit]

    def count(
        self,
        organization_id: int | None = None,
        status: str | None = None,
    ) -> int:
        """Count jobs matching criteria."""
        if organization_id is not None and status:
            org_ids = self._redis.smembers(self._org_key(organization_id))
            status_ids = self._redis.smembers(self._status_key(status))
            return len(org_ids & status_ids)
        elif organization_id is not None:
            return self._redis.scard(self._org_key(organization_id))  # type: ignore[no-any-return]
        elif status:
            return self._redis.scard(self._status_key(status))  # type: ignore[no-any-return]
        else:
            # Count all jobs (sum of all statuses)
            total = 0
            for s in VALID_JOB_STATUSES:
                total += self._redis.scard(self._status_key(s))
            return total

    def cleanup_stale(
        self,
        timeout_seconds: int = 300,
        steal_for_worker: str | None = None,
    ) -> int:
        """Clean up stale running jobs."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        count = 0

        # Get all running job IDs
        running_ids = self._redis.smembers(self._status_key("running"))

        for job_id_str in running_ids:
            job_id = int(job_id_str)
            job_key = self._job_key(job_id)

            # Check heartbeat timestamp
            heartbeat_str = self._redis.hget(job_key, "heartbeat_at")
            if heartbeat_str:
                heartbeat = datetime.fromisoformat(heartbeat_str)
                if heartbeat > cutoff:
                    continue  # Job is still alive

            # Check started_at as fallback
            started_str = self._redis.hget(job_key, "started_at")
            if started_str:
                started = datetime.fromisoformat(started_str)
                if started > cutoff and not heartbeat_str:
                    continue  # Job just started

            # Job is stale - handle it
            if steal_for_worker:
                # Reassign to the specified worker
                self._redis.hset(
                    job_key,
                    mapping={
                        "worker_id": steal_for_worker,
                        "heartbeat_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            else:
                # Release back to pending or fail
                attempts = int(self._redis.hget(job_key, "attempts") or "0")
                max_attempts = int(self._redis.hget(job_key, "max_attempts") or "3")

                if attempts < max_attempts:
                    self.release_job(job_id)
                else:
                    self.fail(
                        job_id, f"Job timed out after {timeout_seconds} seconds", requeue=False
                    )

            count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} stale jobs")

        return count

    def delete_old(self, days: int = 30) -> int:
        """Delete old completed/failed/cancelled jobs."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        count = 0

        for status in ["completed", "failed", "cancelled"]:
            job_ids = self._redis.smembers(self._status_key(status))

            for job_id_str in job_ids:
                job_id = int(job_id_str)
                job_key = self._job_key(job_id)

                completed_str = self._redis.hget(job_key, "completed_at")
                if completed_str:
                    completed = datetime.fromisoformat(completed_str)
                    if completed < cutoff:
                        # Get org_id before deleting
                        org_id = self._redis.hget(job_key, "organization_id")

                        pipe = self._redis.pipeline()
                        pipe.delete(job_key)
                        pipe.srem(self._status_key(status), job_id)
                        if org_id:
                            pipe.srem(self._org_key(int(org_id)), job_id)
                        pipe.execute()

                        count += 1

        if count > 0:
            logger.info(f"Deleted {count} old jobs")

        return count
