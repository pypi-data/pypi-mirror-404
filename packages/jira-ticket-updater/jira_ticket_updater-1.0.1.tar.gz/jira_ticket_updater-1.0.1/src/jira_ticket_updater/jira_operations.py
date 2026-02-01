"""Jira Operations v1.0.0 - High-level Jira operations and workflows with automatic field updates."""

import re
import time
from typing import Optional

from .jira_utils import jira_logger
from .jira_api import (
    get_jira_transitions, transition_jira_issue, get_ticket_details,
    get_code_changes_field_value, update_code_changes_field,
    get_testcase_link_field_value, update_testcase_link_field,
    get_implementor_field_value, get_code_reviewer_field_value,
    update_assignee_field, get_issue_comments
)


def display_issue_status(issue_key: str) -> bool:
    """Display current status and available transitions for an issue."""
    try:
        jira_logger.info("=" * 60)
        jira_logger.info(f"Status Information for Issue: {issue_key}")
        jira_logger.info("=" * 60)

        if not re.match(r'^[A-Z]+-\d+$', issue_key):
            jira_logger.error(f"Invalid issue key format: {issue_key}. Must be in PROJECT-NUMBER format")
            return False
        ticket_details = get_ticket_details(issue_key)
        if not ticket_details:
            jira_logger.error(f"Failed to retrieve issue {issue_key}")
            return False

        current_status = ticket_details.get("status", "Unknown")
        issue_summary = ticket_details.get("summary", "Unknown")
        assignee = ticket_details.get("assignee", "Unassigned")

        jira_logger.info(f"Summary: {issue_summary}")
        jira_logger.info(f"Current Status: {current_status}")
        jira_logger.info(f"Assignee: {assignee}")
        jira_logger.info("")

        transitions = get_jira_transitions(issue_key)
        if not transitions:
            jira_logger.warning(f"No transitions available for issue {issue_key}")
            return True

        jira_logger.info("Available Status Transitions:")
        for i, transition in enumerate(transitions, 1):
            status_name = transition.get("name", "Unknown")
            jira_logger.info(f"  {i}. {status_name}")

        jira_logger.info("")
        status_recommendations = {
            "new": "To Do",
            "to do": "In Progress",
            "in progress": "Development Complete",
            "ready for code review": "Begin Code Review",
            "in code review": "Done"
        }

        recommended_status = status_recommendations.get(current_status.lower())
        if recommended_status:
            # Check if the recommended status is actually available
            available_status_names = [t.get("name", "").lower() for t in transitions]
            if recommended_status.lower() in available_status_names:
                jira_logger.info(f"💡 Recommended Next Status: {recommended_status}")
                jira_logger.info("   (Based on typical workflow progression)")
            else:
                jira_logger.info(f"💡 Typical next status would be '{recommended_status}', but it's not currently available")
        else:
            jira_logger.info("💡 No specific recommendation for current status")

        return True

    except Exception as e:
        jira_logger.error(f"Error displaying status for issue {issue_key}: {str(e)}")
        return False


def display_issue_comments(issue_key: str) -> bool:
    """Display all comments from a Jira issue in a formatted way."""
    try:
        jira_logger.info("=" * 60)
        jira_logger.info(f"Comments for Issue: {issue_key}")
        jira_logger.info("=" * 60)

        comments = get_issue_comments(issue_key)
        if not comments:
            jira_logger.info("No comments found for this issue.")
            return True

        jira_logger.info(f"Total Comments: {len(comments)}")
        jira_logger.info("-" * 40)

        for i, comment in enumerate(comments, 1):
            jira_logger.info(f"Comment #{i}")
            jira_logger.info(f"Author: {comment['author']}")
            jira_logger.info(f"Created: {comment['created']}")
            if comment['updated'] != comment['created']:
                jira_logger.info(f"Updated: {comment['updated']}")
            jira_logger.info(f"Body: {comment['body']}")
            jira_logger.info("-" * 40)

        return True

    except Exception as e:
        jira_logger.error(f"Error displaying comments for issue {issue_key}: {str(e)}")
        return False


def update_jira_status(
    issue_key: str, target_status: str, comment: Optional[str] = None
) -> bool:
    """Update the status of a Jira issue with automatic field population and 3-second API rate limiting."""
    try:

        if not re.match(r"^[A-Z]+-\d+$", issue_key):
            jira_logger.error(
                f"Invalid issue key format: {issue_key}. Must be in PROJECT-NUMBER format"
            )
            return False
        ticket_details = get_ticket_details(issue_key)
        if not ticket_details:
            jira_logger.error(f"Failed to retrieve issue {issue_key}")
            return False

        current_status = ticket_details.get("status", "")
        issue_summary = ticket_details.get("summary", "")
        jira_logger.info(f"Current status: '{current_status}'")
        jira_logger.info(f"Target status: '{target_status}'")
        if current_status and target_status and current_status.strip().lower() == target_status.strip().lower():
            jira_logger.info(f"ℹ️  Issue {issue_key} already in status '{current_status}'")
            return True
        code_changes_value = get_code_changes_field_value(issue_key)
        if not code_changes_value or code_changes_value.strip() == "":
            jira_logger.info("Code Changes field is empty, updating with issue title...")
            if issue_summary:
                update_code_changes_field(issue_key, issue_summary)
                time.sleep(3)  # v1.0.0: API rate limiting protection
            else:
                jira_logger.warning("Issue summary is empty, cannot update Code Changes field")
        else:
            jira_logger.info("Code Changes field already has content, skipping update")

        testcase_link_value = get_testcase_link_field_value(issue_key)
        if not testcase_link_value or testcase_link_value.strip() == "":
            jira_logger.info("Link to Test Case field is empty, setting to 'http://na.com'...")
            update_testcase_link_field(issue_key, "http://na.com")
            time.sleep(3)  # v1.0.0: API rate limiting protection
        else:
            jira_logger.info("Link to Test Case field already has content, skipping update")
        # v1.0.0: Automatic assignee field updates based on target status
        if target_status.lower() in ["to do", "in progress"]:
            implementor_value = get_implementor_field_value(issue_key)
            if implementor_value and implementor_value.get("accountId"):
                implementor_account_id = implementor_value.get("accountId")
                implementor_display_name = implementor_value.get(
                    "displayName", "Unknown"
                )
                jira_logger.info(
                    f"Implementor field has value ({implementor_display_name}), setting as Assignee..."
                )
                update_assignee_field(issue_key, implementor_account_id)
                time.sleep(3)  # v1.0.0: API rate limiting protection
            else:
                jira_logger.info(
                    "Implementor field is empty or has no accountId, skipping Assignee update"
                )

        elif target_status.lower() in ["development complete", "done", "begin code review"]:
            code_reviewer_value = get_code_reviewer_field_value(issue_key)
            if code_reviewer_value and code_reviewer_value.get("accountId"):
                reviewer_account_id = code_reviewer_value.get("accountId")
                reviewer_display_name = code_reviewer_value.get(
                    "displayName", "Unknown"
                )
                jira_logger.info(
                    f"Code Reviewer field has value ({reviewer_display_name}), setting as Assignee..."
                )
                update_assignee_field(issue_key, reviewer_account_id)
                time.sleep(3)  # v1.0.0: API rate limiting protection
            else:
                jira_logger.info(
                    "Code Reviewer field is empty or has no accountId, skipping Assignee update"
                )
        transitions = get_jira_transitions(issue_key)
        if not transitions:
            jira_logger.error(f"❌ No transitions available for issue {issue_key}")
            if comment and comment.strip():
                jira_logger.warning(f"Cannot add comment '{comment.strip()}' - no transitions available")
            return False

        available_statuses = [t.get("name", "") for t in transitions]
        jira_logger.info(f"Available transitions: {', '.join(available_statuses)}")
        target_available = any(t.get("name", "").lower() == target_status.lower() for t in transitions)
        if not target_available:
            jira_logger.error(f"❌ Status '{target_status}' not available for issue {issue_key}")
            jira_logger.info(f"Available: {', '.join(available_statuses)}")
            return False
        success = transition_jira_issue(issue_key, target_status, comment)

        if success:
            jira_logger.info(
                f"Successfully updated issue {issue_key} to status '{target_status}'"
            )
            return True
        else:
            jira_logger.error(
                f"Failed to update issue {issue_key} to status '{target_status}'"
            )
            return False

    except Exception as e:
        jira_logger.error(f"Error updating status for issue {issue_key}: {str(e)}")
        return False