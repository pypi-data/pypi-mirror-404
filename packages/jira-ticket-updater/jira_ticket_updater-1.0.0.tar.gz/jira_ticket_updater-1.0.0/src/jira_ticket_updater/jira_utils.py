"""Jira Utilities v1.0.0 - Core utilities for Jira Ticket Updater including logging and field mapping."""

import base64
import logging
import os
from logging.handlers import RotatingFileHandler

# Configuration Variables - Replace with your actual values
JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
LOGS_DIR = "logs"
LOG_FILE = f"{LOGS_DIR}/jira_status_updater.log"

# Global variables
jira_email = ""
jira_token = ""
jira_base_url = JIRA_BASE_URL
project_key = "PROJECT"

# Custom Field IDs
CUSTOMFIELD_CODE_CHANGES = "customfield_13242"
CUSTOMFIELD_TESTCASE_LINK = "customfield_13292"
CUSTOMFIELD_IMPLEMENTOR = "customfield_10810"
CUSTOMFIELD_CODE_REVIEWER = "customfield_13244"


class JiraStatusLogger:
    """Custom logger for Jira status updater operations."""

    def __init__(self):
        self.logger = logging.getLogger("jira_status_logger")
        self.logger.setLevel(logging.INFO)
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(log_format, date_format)
        max_bytes = 10 * 1024 * 1024
        backup_count = 5
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def debug(self, message: str) -> None:
        self.logger.debug(message)


jira_logger = JiraStatusLogger()


def setup_jira_auth():
    """Set up Jira authentication and return headers."""
    global jira_email, jira_token

    jira_email = JIRA_EMAIL
    jira_token = JIRA_API_TOKEN

    if jira_email and jira_token:
        jira_credentials = base64.b64encode(
            f"{jira_email}:{jira_token}".encode()
        ).decode()
        return {
            "Authorization": f"Basic {jira_credentials}",
            "Content-Type": "application/json",
        }
    else:
        return {"Content-Type": "application/json"}


jira_headers = setup_jira_auth()


def extract_text_from_jira_field(field_value) -> str:
    """Extract text content from Jira field values."""
    if not field_value:
        return ""

    if isinstance(field_value, str):
        return field_value

    if isinstance(field_value, dict):
        return extract_text_from_adf(field_value)

    return str(field_value)


def extract_text_from_adf(adf_object: dict) -> str:
    """Extract plain text from Atlassian Document Format (ADF)."""
    text_parts = []

    try:
        node_type = adf_object.get("type", "")

        if node_type == "text":
            text = adf_object.get("text", "")
            text_parts.append(text)

        elif node_type in [
            "paragraph",
            "heading",
            "bulletList",
            "orderedList",
            "listItem",
        ]:
            content = adf_object.get("content", [])
            for child in content:
                if isinstance(child, dict):
                    text_parts.append(extract_text_from_adf(child))

        elif "content" in adf_object:
            content = adf_object.get("content", [])
            for item in content:
                if isinstance(item, dict):
                    text_parts.append(extract_text_from_adf(item))

    except Exception as e:
        logging.warning(f"Error extracting text from ADF object: {str(e)}")
        return ""

    return " ".join(text_parts).strip()