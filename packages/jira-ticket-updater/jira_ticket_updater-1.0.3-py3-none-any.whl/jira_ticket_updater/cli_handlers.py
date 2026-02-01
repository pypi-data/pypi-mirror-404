"""CLI Handlers v1.0.0 - Command-line interface handlers and argument parsing for Jira Ticket Updater."""

import re
import time

from .jira_utils import jira_logger
from .jira_api import (
    add_comment_to_issue, update_assignee_field, get_implementor_field_value
)
from .jira_operations import display_issue_comments
from .jira_operations import display_issue_status, update_jira_status


def parse_arguments(args: list) -> dict:
    """Parse command line arguments for Jira Ticket Updater v1.0.3 and return a dictionary with parsed values."""
    if len(args) < 1:
        jira_logger.error("Usage: jira-ticket-updater <issue_key> [--status <status>] [--comment [comment_text]]")
        jira_logger.info("")
        jira_logger.info("Arguments:")
        jira_logger.info("  issue_key         - Jira issue key (e.g., PROJ-123) or branch name containing issue key")
        jira_logger.info("  --status STATUS   - Update issue status to STATUS")
        jira_logger.info("  --comment         - Show current comments on the issue")
        jira_logger.info("  --comment TEXT    - Add a new comment to the issue")
        jira_logger.info("")
        jira_logger.info("Examples:")
        jira_logger.info("  jira-ticket-updater PROJ-123                           # Show status and recommendations")
        jira_logger.info("  jira-ticket-updater PROJ-123 --comment                 # Show current comments")
        jira_logger.info("  jira-ticket-updater PROJ-123 --comment \"Work started\"    # Add new comment")
        jira_logger.info("  jira-ticket-updater PROJ-123 --status \"In Progress\"     # Update status")
        jira_logger.info("  jira-ticket-updater PROJ-123 --status \"Done\" --comment \"Completed\"  # Update status + comment")
        return None

    issue_input = args[0].strip()
    remaining_args = args[1:]

    # Initialize parsed arguments
    parsed = {
        'issue_input': issue_input,
        'target_status': None,
        'comment_action': None,  # None, 'show', or 'add'
        'comment_text': None
    }

    i = 0
    while i < len(remaining_args):
        arg = remaining_args[i]

        if arg == '--status':
            if i + 1 < len(remaining_args):
                parsed['target_status'] = remaining_args[i + 1].strip()
                i += 2
            else:
                jira_logger.error("Error: --status requires a status value")
                return None

        elif arg == '--comment':
            if i + 1 < len(remaining_args) and not remaining_args[i + 1].startswith('-'):
                # Has comment text - add comment
                parsed['comment_action'] = 'add'
                parsed['comment_text'] = remaining_args[i + 1].strip()
                i += 2
            else:
                # No text after --comment - show comments
                parsed['comment_action'] = 'show'
                i += 1
        else:
            jira_logger.error(f"Unknown argument: {arg}")
            jira_logger.error("Use --status or --comment flags")
            return None

    return parsed


def handle_status_and_comment(issue_key: str, target_status: str, comment_text: str) -> bool:
    """Handle combined status update and comment addition with 3-second API rate limiting."""
    jira_logger.info(f"Processing issue: {issue_key}")
    jira_logger.info(f"Target status: {target_status}")
    jira_logger.info(f"Comment to be added: '{comment_text}'")

    status_success = update_jira_status(issue_key, target_status, None)

    if status_success:
        # Special handling for "To Do" status - wait for Jira automation to complete and update assignee again
        # v1.0.0: Uses 3-second delays to prevent API rate limiting
        if target_status.lower() == "to do":
            time.sleep(3)  # Allow Jira automation to complete
            implementor_value = get_implementor_field_value(issue_key)
            if implementor_value and implementor_value.get("accountId"):
                implementor_account_id = implementor_value.get("accountId")
                implementor_display_name = implementor_value.get("displayName", "Unknown")
                jira_logger.info(f"Re-setting assignee to implementor ({implementor_display_name})")
                update_assignee_field(issue_key, implementor_account_id)
                time.sleep(3)  # API rate limiting protection
            else:
                jira_logger.info("Implementor field not available for re-assignment")

        # Wait 3 seconds before adding comment (API rate limiting protection)
        time.sleep(3)
        comment_success = add_comment_to_issue(issue_key, comment_text)

        success = comment_success
        if comment_success:
            jira_logger.info("✅ Status updated and comment added successfully")
        else:
            jira_logger.warning("⚠️ Status updated but comment addition failed")
    else:
        success = False
        jira_logger.error("❌ Status update failed, skipping comment addition")

    return success


def handle_status_update(issue_key: str, target_status: str) -> bool:
    """Handle status update only with 3-second API rate limiting for assignee field updates."""
    jira_logger.info(f"Processing issue: {issue_key}")
    jira_logger.info(f"Target status: {target_status}")

    success = update_jira_status(issue_key, target_status, None)

    # Special handling for "To Do" status - wait for Jira automation to complete and update assignee again
    # v1.0.0: Uses 3-second delays to prevent API rate limiting
    if success and target_status.lower() == "to do":
        time.sleep(3)  # Allow Jira automation to complete
        implementor_value = get_implementor_field_value(issue_key)
        if implementor_value and implementor_value.get("accountId"):
            implementor_account_id = implementor_value.get("accountId")
            implementor_display_name = implementor_value.get("displayName", "Unknown")
            jira_logger.info(f"Re-setting assignee to implementor ({implementor_display_name})")
            update_assignee_field(issue_key, implementor_account_id)
            time.sleep(3)  # API rate limiting protection
        else:
            jira_logger.info("Implementor field not available for re-assignment")

    return success


def handle_comment_operation(issue_key: str, comment_action: str, comment_text: str = None) -> bool:
    """Handle comment operations (add or show)."""
    if comment_action == 'add' and comment_text:
        # Comment addition only
        jira_logger.info(f"Adding comment to issue {issue_key}")
        success = add_comment_to_issue(issue_key, comment_text)
    elif comment_action == 'show':
        # Display existing comments
        success = display_issue_comments(issue_key)
    else:
        jira_logger.error("Invalid comment operation")
        success = False

    return success


def handle_default_display(issue_key: str) -> bool:
    """Handle default status information display."""
    return display_issue_status(issue_key)


def extract_issue_key_from_input(input_arg: str) -> str:
    """Extract issue key from various input formats."""
    if not input_arg or not isinstance(input_arg, str):
        return ""

    # Check if it's already an issue key (format: PROJECT-123)
    issue_key_pattern = r"^[A-Z]+-\d+$"
    if re.match(issue_key_pattern, input_arg):
        return input_arg.upper()

    # Try to extract from branch name format
    pattern = r"[A-Z]+-\d+"
    match = re.search(pattern, input_arg, re.IGNORECASE)
    if match:
        return match.group(0).upper()

    return ""


def process_issue_operation(parsed_args: dict) -> bool:
    """Process the issue operation based on parsed arguments."""
    issue_key = extract_issue_key_from_input(parsed_args['issue_input'])
    if not issue_key:
        jira_logger.error(f"Could not extract valid issue key from: {parsed_args['issue_input']}")
        jira_logger.info("Issue key should be in format PROJECT-NUMBER (e.g., PROJ-123)")
        return False

    # Priority: combined operations > single operations > default
    if parsed_args['target_status'] and parsed_args['comment_text']:
        # Both status update and comment addition requested
        return handle_status_and_comment(issue_key, parsed_args['target_status'], parsed_args['comment_text'])

    elif parsed_args['target_status']:
        # Status update only
        return handle_status_update(issue_key, parsed_args['target_status'])

    elif parsed_args['comment_action'] == 'add' and parsed_args['comment_text']:
        # Comment addition only
        return handle_comment_operation(issue_key, parsed_args['comment_action'], parsed_args['comment_text'])

    elif parsed_args['comment_action'] == 'show':
        # Display existing comments
        return handle_comment_operation(issue_key, parsed_args['comment_action'])

    else:
        # Display status information only (default action)
        return handle_default_display(issue_key)