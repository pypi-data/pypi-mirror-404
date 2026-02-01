"""Jira API v1.0.0 - REST API interaction functions for Jira operations with comprehensive field mapping."""

import requests
from typing import Any, Dict, Optional

from .jira_utils import jira_logger, jira_headers, JIRA_BASE_URL, extract_text_from_jira_field
from .jira_utils import CUSTOMFIELD_CODE_CHANGES, CUSTOMFIELD_TESTCASE_LINK
from .jira_utils import CUSTOMFIELD_IMPLEMENTOR, CUSTOMFIELD_CODE_REVIEWER


def get_jira_transitions(issue_key: str) -> list:
    """Get available status transitions for a Jira issue."""
    transitions = []

    try:
        url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
        resp = requests.get(url, headers=jira_headers, timeout=30)

        if resp.status_code == 200:
            data = resp.json()
            transitions = data.get("transitions", [])
        else:
            jira_logger.error(
                f"Failed to get transitions for {issue_key}: {resp.status_code} {resp.text}"
            )

    except Exception as e:
        jira_logger.error(f"Error getting transitions for {issue_key}: {str(e)}")

    return transitions


def transition_jira_issue(
    issue_key: str, target_status: str, comment: Optional[str] = None
) -> bool:
    """Transition a Jira issue to a new status."""
    try:
        transitions = get_jira_transitions(issue_key)
        if not transitions:
            jira_logger.error(f"No transitions available for issue {issue_key}")
            return False

        transition_id = None
        for transition in transitions:
            if transition.get("name", "").lower() == target_status.lower():
                transition_id = transition.get("id")
                break

        if not transition_id:
            jira_logger.error(
                f"Status '{target_status}' not available for issue {issue_key}"
            )
            jira_logger.info(
                f"Available statuses: {[t.get('name') for t in transitions]}"
            )
            return False

        payload = {"transition": {"id": transition_id}}
        if comment and comment.strip():
            # Format comment as Atlassian Document Format (ADF)
            adf_comment = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment.strip()
                            }
                        ]
                    }
                ]
            }
            payload["update"] = {"comment": [{"add": {"body": adf_comment}}]}
        url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
        resp = requests.post(url, headers=jira_headers, json=payload, timeout=30)

        if resp.status_code == 204:
            jira_logger.info(
                f"✅ Successfully transitioned issue {issue_key} to status '{target_status}'"
            )
            if comment and comment.strip():
                jira_logger.info(f"✅ Comment added: '{comment.strip()}'")
            return True
        else:
            jira_logger.error(
                f"❌ Failed to transition issue {issue_key} to status '{target_status}': {resp.status_code}"
            )
            if resp.text:
                jira_logger.error(f"Details: {resp.text}")
            return False

    except Exception as e:
        jira_logger.error(f"Error transitioning issue {issue_key}: {str(e)}")
        return False


def get_ticket_details(issue_key: str) -> Dict[str, Any]:
    """Get basic details for a Jira issue."""
    ticket_details = {
        "issue_key": issue_key,
        "summary": "",
        "status": "",
        "assignee": "",
        "reporter": "",
        "description": "",
    }

    try:
        jira_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
        resp = requests.get(jira_url, headers=jira_headers, timeout=30)

        if resp.status_code == 200:
            issue_data = resp.json()
            fields = issue_data.get("fields", {})

            ticket_details["summary"] = fields.get("summary", "")
            ticket_details["description"] = extract_text_from_jira_field(
                fields.get("description", "")
            )
            status = fields.get("status")
            if status and isinstance(status, dict):
                ticket_details["status"] = status.get("name", "")

            assignee = fields.get("assignee")
            if assignee and isinstance(assignee, dict):
                ticket_details["assignee"] = assignee.get("displayName", "")
            reporter = fields.get("reporter")
            if reporter and isinstance(reporter, dict):
                ticket_details["reporter"] = reporter.get("displayName", "")
            else:
                creator = fields.get("creator")
                if creator and isinstance(creator, dict):
                    ticket_details["reporter"] = creator.get("displayName", "")

        else:
            jira_logger.error(
                f"Failed to retrieve ticket details for {issue_key}: {resp.status_code} {resp.text}"
            )

    except Exception as e:
        jira_logger.error(f"Error retrieving ticket details for {issue_key}: {str(e)}")

    return ticket_details


def get_code_changes_field_value(issue_key: str) -> str:
    """Get the current value of the Code Changes field."""
    try:
        jira_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
        resp = requests.get(jira_url, headers=jira_headers, timeout=30)

        if resp.status_code == 200:
            issue_data = resp.json()
            code_changes_field = issue_data.get("fields", {}).get(
                CUSTOMFIELD_CODE_CHANGES
            )
            if code_changes_field:
                return extract_text_from_jira_field(code_changes_field)
            else:
                return ""
        else:
            jira_logger.warning(
                f"Could not retrieve Code Changes field for {issue_key}: {resp.status_code}"
            )
            return ""

    except Exception as e:
        jira_logger.warning(
            f"Error retrieving Code Changes field for {issue_key}: {str(e)}"
        )
        return ""


def update_code_changes_field(issue_key: str, code_changes: str) -> bool:
    """Update the Code Changes field with the provided value."""
    try:
        jira_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"

        # Create ADF content for the description field
        adf_content = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": code_changes}],
                }
            ],
        }

        update_payload = {"fields": {CUSTOMFIELD_CODE_CHANGES: adf_content}}
        resp = requests.put(
            jira_url, headers=jira_headers, json=update_payload, timeout=30
        )

        if resp.status_code in (200, 204):
            jira_logger.info(f"Updated Code Changes field for issue {issue_key}")
            return True
        else:
            jira_logger.warning(
                f"Failed to update Code Changes field for {issue_key}: {resp.status_code}"
            )
            return False

    except Exception as e:
        jira_logger.warning(
            f"Error updating Code Changes field for {issue_key}: {str(e)}"
        )
        return False


def get_testcase_link_field_value(issue_key: str) -> str:
    """Get the current value of the Link to Test Case field."""
    try:
        jira_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
        resp = requests.get(jira_url, headers=jira_headers, timeout=30)

        if resp.status_code == 200:
            issue_data = resp.json()
            testcase_link_field = issue_data.get("fields", {}).get(
                CUSTOMFIELD_TESTCASE_LINK
            )
            if testcase_link_field:
                # Handle both string and object formats
                if isinstance(testcase_link_field, dict):
                    return testcase_link_field.get("url", "")
                else:
                    return str(testcase_link_field)
            else:
                return ""
        else:
            jira_logger.warning(
                f"Could not retrieve Link to Test Case field for {issue_key}: {resp.status_code}"
            )
            return ""

    except Exception as e:
        jira_logger.warning(
            f"Error retrieving Link to Test Case field for {issue_key}: {str(e)}"
        )
        return ""


def update_testcase_link_field(issue_key: str, link_value: str) -> bool:
    """Update the Link to Test Case field with the provided value."""
    try:
        jira_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"

        update_payload = {"fields": {CUSTOMFIELD_TESTCASE_LINK: link_value}}
        resp = requests.put(
            jira_url, headers=jira_headers, json=update_payload, timeout=30
        )

        if resp.status_code in (200, 204):
            jira_logger.info(
                f"Updated Link to Test Case field for issue {issue_key} to '{link_value}'"
            )
            return True
        else:
            jira_logger.warning(
                f"Failed to update Link to Test Case field for {issue_key}: {resp.status_code}"
            )
            return False

    except Exception as e:
        jira_logger.warning(
            f"Error updating Link to Test Case field for {issue_key}: {str(e)}"
        )
        return False


def get_implementor_field_value(issue_key: str) -> dict:
    """Get the current value of the Implementor field."""
    try:
        jira_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
        resp = requests.get(jira_url, headers=jira_headers, timeout=30)

        if resp.status_code == 200:
            issue_data = resp.json()
            implementor_field = issue_data.get("fields", {}).get(
                CUSTOMFIELD_IMPLEMENTOR
            )
            if implementor_field and isinstance(implementor_field, dict):
                return implementor_field
            else:
                return {}
        else:
            jira_logger.warning(
                f"Could not retrieve Implementor field for {issue_key}: {resp.status_code}"
            )
            return {}

    except Exception as e:
        jira_logger.warning(
            f"Error retrieving Implementor field for {issue_key}: {str(e)}"
        )
        return {}


def update_assignee_field(issue_key: str, assignee_account_id: str) -> bool:
    """Update the Assignee field with the provided account ID."""
    try:
        jira_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"

        # Prepare assignee payload
        assignee_payload = {"accountId": assignee_account_id}
        update_payload = {"fields": {"assignee": assignee_payload}}

        resp = requests.put(
            jira_url, headers=jira_headers, json=update_payload, timeout=30
        )

        if resp.status_code in (200, 204):
            jira_logger.info(f"Updated Assignee field for issue {issue_key}")
            return True
        else:
            jira_logger.warning(
                f"Failed to update Assignee field for {issue_key}: {resp.status_code}"
            )
            return False

    except Exception as e:
        jira_logger.warning(f"Error updating Assignee field for {issue_key}: {str(e)}")
        return False


def get_code_reviewer_field_value(issue_key: str) -> dict:
    """Get the current value of the Code Reviewer field."""
    try:
        jira_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
        resp = requests.get(jira_url, headers=jira_headers, timeout=30)

        if resp.status_code == 200:
            issue_data = resp.json()
            code_reviewer_field = issue_data.get("fields", {}).get(
                CUSTOMFIELD_CODE_REVIEWER
            )
            if code_reviewer_field and isinstance(code_reviewer_field, dict):
                return code_reviewer_field
            else:
                return {}
        else:
            jira_logger.warning(
                f"Could not retrieve Code Reviewer field for {issue_key}: {resp.status_code}"
            )
            return {}

    except Exception as e:
        jira_logger.warning(
            f"Error retrieving Code Reviewer field for {issue_key}: {str(e)}"
        )
        return {}


def get_issue_comments(issue_key: str) -> list:
    """Get all comments from a Jira issue."""
    comments_list = []

    try:
        comments_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
        resp = requests.get(comments_url, headers=jira_headers, timeout=30)

        if resp.status_code == 200:
            comments_data = resp.json()
            comments = comments_data.get('comments', [])

            for comment in comments:
                comment_info = {
                    'id': comment.get('id', ''),
                    'author': comment.get('author', {}).get('displayName', 'Unknown'),
                    'body': extract_text_from_jira_field(comment.get('body', '')),
                    'created': comment.get('created', ''),
                    'updated': comment.get('updated', '')
                }
                comments_list.append(comment_info)

            jira_logger.info(f"Retrieved {len(comments_list)} comments from issue {issue_key}")
            return comments_list
        else:
            jira_logger.error(f"Failed to retrieve comments for {issue_key}: {resp.status_code} {resp.text}")
            return []

    except Exception as e:
        jira_logger.error(f"Error retrieving comments for {issue_key}: {str(e)}")
        return []


def add_comment_to_issue(issue_key: str, comment: str) -> bool:
    """Add a comment to a Jira issue."""
    if not comment or not comment.strip():
        jira_logger.warning("Cannot add empty comment")
        return False

    if not issue_key or not issue_key.strip():
        jira_logger.error("Invalid issue key provided")
        return False

    try:
        # Format comment as Atlassian Document Format (ADF)
        adf_comment = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": comment.strip()
                        }
                    ]
                }
            ]
        }

        comment_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
        comment_payload = {"body": adf_comment}

        resp = requests.post(comment_url, headers=jira_headers, json=comment_payload, timeout=30)

        if resp.status_code in (200, 201):
            jira_logger.info(f"✅ Comment added to issue {issue_key}")
            return True
        else:
            jira_logger.error(f"❌ Failed to add comment: {resp.status_code}")
            return False

    except Exception as e:
        jira_logger.error(f"❌ Error adding comment to {issue_key}: {str(e)}")
        return False


def add_comment_separately(issue_key: str, comment: str) -> bool:
    """Add a comment to an issue (deprecated, use add_comment_to_issue)."""
    return add_comment_to_issue(issue_key, comment)