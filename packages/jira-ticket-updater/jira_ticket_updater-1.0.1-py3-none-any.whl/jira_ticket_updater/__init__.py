"""Jira Ticket Updater v1.0.0 - A command-line tool for updating Jira ticket status with workflow transitions and optional comments."""

__version__ = "1.0.1"
__author__ = "Pandiyaraj Karuppasamy"
__email__ = "pandiyarajk@live.com"
__description__ = "A command-line tool for updating Jira ticket status"

from .jira_api import (
    add_comment_to_issue,
    get_issue_comments,
)

from .jira_operations import (
    display_issue_comments,
    update_jira_status,
    display_issue_status,
)
