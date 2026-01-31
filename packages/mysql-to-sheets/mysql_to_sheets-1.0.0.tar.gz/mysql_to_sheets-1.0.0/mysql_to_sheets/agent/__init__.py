"""Hybrid Agent for MySQL to Sheets Sync.

The agent enables customers to run syncs within their infrastructure
without exposing databases to the internet. It polls the SaaS control
plane for jobs, executes queries locally, and pushes results directly
to Google Sheets.

Security Model:
- Raw database credentials never touch the control plane
- LINK_TOKEN authenticates agent to control plane
- All database connections are local to customer network

Usage:
    # Via CLI
    python -m mysql_to_sheets.agent run

    # Via Docker
    docker run -e LINK_TOKEN=... mysql-to-sheets-agent

    # Programmatic
    from mysql_to_sheets.agent import AgentWorker, run_agent
    run_agent()
"""

from mysql_to_sheets.agent.agent_worker import AgentWorker, run_agent
from mysql_to_sheets.agent.link_config_provider import LinkConfigProvider
from mysql_to_sheets.agent.link_token import (
    LinkTokenInfo,
    LinkTokenStatus,
    validate_link_token,
)

__all__ = [
    "AgentWorker",
    "LinkConfigProvider",
    "LinkTokenInfo",
    "LinkTokenStatus",
    "run_agent",
    "validate_link_token",
]
