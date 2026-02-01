# Jira Ticket Updater v1.0.0

[![PyPI version](https://badge.fury.io/py/jira-ticket-updater.svg)](https://pypi.org/project/jira-ticket-updater/)
[![Python Versions](https://img.shields.io/pypi/pyversions/jira-ticket-updater.svg)](https://pypi.org/project/jira-ticket-updater/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command-line tool for updating Jira ticket status with workflow transitions, automatic field updates, and optional comments. Features 3-second API rate limiting to prevent Jira API throttling.

## Features

- **Issue Key Detection**: Automatically extracts Jira issue keys from branch names or accepts direct issue keys
- **Status Transitions**: Transition Jira issues to any available status in the workflow
- **Comment Support**: Add optional comments during status transitions
- **Validation**: Verifies issue existence and available transitions before attempting updates
- **Comprehensive Logging**: Detailed logging with file and console output for debugging
- **Error Handling**: Robust error handling with informative error messages

## Installation

### From PyPI (Recommended)

```bash
pip install jira-ticket-updater
```

### From Source

```cmd
git clone https://github.com/Pandiyarajk/jira-ticket-updater.git
cd jira-ticket-updater
pip install .
```

### Requirements

- Python 3.7+
- requests>=2.25.0

### Building and Local Installation

For development purposes, you can build and install the package locally using the provided build script:

#### Windows (Command Prompt)
```cmd
build-and-install.bat
```

#### Manual Build Process

If you prefer to build manually:

```bash
# Install build tools (one-time setup)
pip install build

# Build the package
python -m build

# Install locally
pip install .
```

#### Script Options

All build scripts support the following options:

- `clean`: Remove existing build artifacts before building
- `skip-install`: Build the package but skip local installation

Examples:
```cmd
REM Clean and build
build-and-install.bat clean

REM Build only (no install)
build-and-install.bat skip-install
```

## Configuration

The tool requires the following environment variables to be set:

### Required Environment Variables

- `JIRA_BASE_URL`: Your Jira instance URL (e.g., `https://yourcompany.atlassian.net`)
- `JIRA_EMAIL`: Your Jira account email
- `JIRA_API_TOKEN`: Your Jira API token (create one at https://id.atlassian.com/manage-profile/security/api-tokens)

## Usage

### Command Line

```bash
jira-ticket-updater <issue_key> [--status] [status] [--comment] [comment]
```

### Arguments

- `issue_key`: Jira issue key (e.g., `PROJ-123`) or branch name containing an issue key
- `--status STATUS`: Update issue status to the specified STATUS
- `--comment`: Show current comments on the issue
- `--comment TEXT`: Add a new comment to the issue

### Examples

```bash
# Show current status, available transitions, and workflow recommendations
jira-ticket-updater PROJ-123

# Show current comments on the issue
jira-ticket-updater PROJ-123 --comment

# Add a new comment to the issue
jira-ticket-updater PROJ-123 --comment "Started working on this issue"

# Update issue status
jira-ticket-updater PROJ-123 --status "In Progress"

# Update issue status
jira-ticket-updater PROJ-123 --status "In Progress"

# Update issue status with a comment
jira-ticket-updater PROJ-456 --status "Done" --comment "Implementation completed"

# Combine operations: update status and add comment
jira-ticket-updater PROJ-789 --status "Ready For QA" --comment "Code review passed"
```

#### Status Information Display Example

When running `jira-ticket-updater PROJ-123` (without target status), you get:

```
============================================================
Status Information for Issue: PROJ-123
============================================================
Summary: Implement user authentication feature
Current Status: To Do
Assignee: John Doe

Available Status Transitions:
  1. In Progress
  2. Done
  3. Ready For QA
  4. Closed

💡 Recommended Next Status: In Progress
   (Based on typical workflow progression)

============================================================
Status information retrieved successfully
============================================================
```

### Special Behavior

**Status Recommendations**: When displaying issue status information (without target status), the tool provides workflow-based recommendations for the next logical status transition.

#### Workflow Status Table

The tool provides intelligent status recommendations based on typical development workflow progression:

| Current Status | Recommended Next Status | Available Transitions |
|----------------|-------------------------|----------------------|
| **New** | To Do | To Do, In Progress, Done, etc. |
| **To Do** | In Progress | In Progress, Done, Ready For QA, etc. |
| **In Progress** | Development Complete | Development Complete, Done, Ready For QA, etc. |
| **Development Complete** | Begin Code Review | Begin Code Review, Done, Ready For QA, etc. |
| **Ready for Code Review** | Begin Code Review | Begin Code Review, Done, Ready For QA, etc. |
| **Begin Code Review** | Done | Done, Ready For QA, Closed, etc. |
| **In Code Review** | Done | Done, Ready For QA, Closed, etc. |

**Note**: Recommendations are only shown if the suggested status is actually available for the specific issue's workflow.

**Auto Field Updates**: The tool automatically performs field updates based on status transitions:

**For ALL status transitions (if fields are empty):**
- **Code Changes Field**: Populated with the issue's title/summary (to start work tracking)
- **Link to Test Case Field**: Set to "http://na.com" (as a placeholder)

**Assignee Field Updates by Status:**
- **For transitions to "To Do" or "In Progress"**: Set to the value from the Implementor field if available
- **For transitions to "Development Complete", "Done", or "Begin Code Review"**: Set to the value from the Code Reviewer field if available

**Combined Operations**: When both status update and comment addition are requested, the tool will:
- Update the status first
- Wait 3 seconds
- Then add the comment separately

**Special "To Do" Status Handling**: When transitioning to "To Do" status, the tool accounts for Jira automation that may clear assignee fields:
- Update the status first
- Wait 3 seconds for Jira automation to complete
- Re-assign the implementor to the assignee field

**Field Update Summary:**
- **Code Changes & Link to Test Case**: Updated for ANY status transition if empty
- **Assignee Field**: Updated based on specific transition rules and field values

This ensures consistent field population throughout the development workflow.

### API Functions

The package provides reusable functions for programmatic use:

#### `add_comment_to_issue(issue_key: str, comment: str) -> bool`

Add a comment to a Jira issue with automatic ADF formatting.

```python
from jira_ticket_updater import add_comment_to_issue

# Add a comment to an issue
success = add_comment_to_issue('PROJ-123', 'This is a test comment')
if success:
    print("Comment added successfully!")

# Can also be used in scripts or automation
import os
os.environ['JIRA_BASE_URL'] = 'https://yourcompany.atlassian.net'
os.environ['JIRA_EMAIL'] = 'your.email@company.com'
os.environ['JIRA_API_TOKEN'] = 'your_api_token'

add_comment_to_issue('PROJ-456', 'Automated comment from script')
```

**Parameters:**
- `issue_key`: Jira issue key (e.g., 'PROJ-123')
- `comment`: Comment text to add

**Returns:** `True` if comment was added successfully, `False` otherwise

#### `get_issue_comments(issue_key: str) -> list`

Retrieve all comments from a Jira issue.

```python
from jira_ticket_updater import get_issue_comments

# Get all comments from an issue
comments = get_issue_comments('PROJ-123')
for comment in comments:
    print(f"{comment['author']}: {comment['body']}")
```

**Parameters:**
- `issue_key`: Jira issue key (e.g., 'PROJ-123')

**Returns:** List of comment dictionaries with 'id', 'author', 'body', 'created', 'updated' keys

#### `display_issue_comments(issue_key: str) -> bool`

Display all comments from a Jira issue in a formatted way.

```python
from jira_ticket_updater import display_issue_comments

# Display comments for an issue
display_issue_comments('PROJ-123')
```

**Parameters:**
- `issue_key`: Jira issue key (e.g., 'PROJ-123')

**Returns:** `True` if comments were displayed successfully, `False` otherwise

#### `update_jira_status(issue_key: str, target_status: str, comment: Optional[str] = None) -> bool`

Update the status of a Jira issue with automatic field population and workflow validation.

```python
from jira_ticket_updater import update_jira_status
import os

# Set up environment variables
os.environ['JIRA_BASE_URL'] = 'https://yourcompany.atlassian.net'
os.environ['JIRA_EMAIL'] = 'your.email@company.com'
os.environ['JIRA_API_TOKEN'] = 'your_api_token'

# Update issue status
success = update_jira_status('PROJ-123', 'In Progress')
if success:
    print("Status updated successfully!")

# Update status with a comment
success = update_jira_status('PROJ-456', 'Done', 'Implementation completed')
```

**Parameters:**
- `issue_key`: Jira issue key (e.g., 'PROJ-123')
- `target_status`: Target status name (e.g., 'In Progress', 'Done', 'To Do')
- `comment`: Optional comment to add during the status transition

**Returns:** `True` if status was updated successfully, `False` otherwise

**Automatic Field Updates:**
- **Code Changes Field**: Populated with issue title (any transition if empty)
- **Link to Test Case Field**: Set to "http://na.com" (any transition if empty)
- **Assignee Field**: Automatically set based on target status:
  - "To Do" or "In Progress" → Set from Implementor field
  - "Development Complete", "Done", "Begin Code Review" → Set from Code Reviewer field

**API Rate Limiting:** Includes 3-second delays after field updates to prevent Jira API throttling.

#### `handle_status_and_comment(issue_key: str, target_status: str, comment_text: str) -> bool`

Combined operation to update issue status and add a comment with proper sequencing and rate limiting.

```python
from jira_ticket_updater.cli_handlers import handle_status_and_comment
import os

# Set up environment variables
os.environ['JIRA_BASE_URL'] = 'https://yourcompany.atlassian.net'
os.environ['JIRA_EMAIL'] = 'your.email@company.com'
os.environ['JIRA_API_TOKEN'] = 'your_api_token'

# Update status and add comment
success = handle_status_and_comment('PROJ-123', 'In Progress', 'Started working on this issue')
```

**Parameters:**
- `issue_key`: Jira issue key (e.g., 'PROJ-123')
- `target_status`: Target status name
- `comment_text`: Comment text to add

**Returns:** `True` if both status update and comment addition succeeded, `False` otherwise

**Behavior:** Updates status first, waits 3 seconds, then adds comment (API rate limiting protection).

#### `handle_status_update(issue_key: str, target_status: str) -> bool`

Update issue status only, with automatic assignee field management for "To Do" status.

```python
from jira_ticket_updater.cli_handlers import handle_status_update
import os

# Set up environment variables
os.environ['JIRA_BASE_URL'] = 'https://yourcompany.atlassian.net'
os.environ['JIRA_EMAIL'] = 'your.email@company.com'
os.environ['JIRA_API_TOKEN'] = 'your_api_token'

# Update status only
success = handle_status_update('PROJ-123', 'To Do')
```

**Parameters:**
- `issue_key`: Jira issue key (e.g., 'PROJ-123')
- `target_status`: Target status name

**Returns:** `True` if status update succeeded, `False` otherwise

**Special "To Do" Handling:** For "To Do" status transitions, waits 3 seconds for Jira automation, then re-assigns the implementor to handle cases where automation clears assignee fields.

#### `update_assignee_field(issue_key: str, assignee_account_id: str) -> bool`

Update the assignee field of a Jira issue.

```python
from jira_ticket_updater.jira_api import update_assignee_field
import os

# Set up environment variables
os.environ['JIRA_BASE_URL'] = 'https://yourcompany.atlassian.net'
os.environ['JIRA_EMAIL'] = 'your.email@company.com'
os.environ['JIRA_API_TOKEN'] = 'your_api_token'

# Update assignee
success = update_assignee_field('PROJ-123', 'account_id_here')
```

**Parameters:**
- `issue_key`: Jira issue key (e.g., 'PROJ-123')
- `assignee_account_id`: Jira user account ID to assign the issue to

**Returns:** `True` if assignee was updated successfully, `False` otherwise

#### Additional Field Update Functions

```python
from jira_ticket_updater.jira_api import (
    update_code_changes_field,
    update_testcase_link_field
)

# Update Code Changes field with issue description
success = update_code_changes_field('PROJ-123', 'Implemented user authentication')

# Update Link to Test Case field
success = update_testcase_link_field('PROJ-456', 'https://testcase.example.com/TC-001')
```

### What the Tool Does

1. **Extracts Issue Key**: Parses the Jira issue key from the input (direct key or from branch name)

2. **Validates Issue**: Verifies the issue exists and retrieves current details from Jira

3. **Auto-Updates Code Changes Field**: When transitioning from "To Do" to "In Progress", automatically populates the Code Changes field with the issue title if it's currently empty

4. **Auto-Updates Link to Test Case Field**: When transitioning from "To Do" to "In Progress", automatically sets the Link to Test Case field to "http://na.com" if it's currently empty

5. **Auto-Updates Assignee Field**: When transitioning to "In Progress", automatically sets the Assignee field to the value from the Implementor field if the Implementor field has a value

6. **Auto-Updates Assignee for Review**: When transitioning from "In Progress" to "Development Complete", automatically sets the Assignee field to the value from the Code Reviewer field if the Code Reviewer field has a value

7. **Auto-Updates Assignee for Code Review**: When transitioning to "Begin Code Review", automatically sets the Assignee field to the value from the Code Reviewer field if the Code Reviewer field has a value

8. **Checks Available Transitions**: Retrieves available status transitions for the issue

5. **Performs Transition**: Transitions the issue to the target status with optional comment

6. **Verification**: Confirms the status update was successful

### Input Formats

The tool accepts issue keys in various formats:

- Direct issue keys: `PROJ-123`, `ABC-456`
- Branch names containing issue keys:
  - `feature/PROJ-123-add-new-feature`
  - `bugfix/ABC-456-fix-bug`
  - `hotfix/DEF-789-security-patch`

## Logging

The tool creates detailed logs in the `logs/` directory:

- **File Logging**: `logs/jira_ticket_updater.log` with rotating files (10MB max, 5 backups)
- **Console Logging**: Real-time output to stdout/stderr
- **Log Levels**: INFO, WARNING, ERROR with timestamps

## API Rate Limiting

The tool includes built-in error handling for API rate limits and network issues.

## Error Handling

- **Network Errors**: Automatic retry logic for temporary network issues
- **Authentication Errors**: Clear error messages for invalid credentials
- **Permission Errors**: Detailed messages for insufficient permissions
- **Invalid Transitions**: Validation of available status transitions
- **Issue Not Found**: Clear messages when issues don't exist

## Development

### Setting up Development Environment

```cmd
git clone https://github.com/Pandiyarajk/jira-ticket-updater.git
cd jira-ticket-updater
python -m venv venv
venv\Scripts\activate
pip install -e .
```

### Running Tests

```cmd
# Run the tool directly
python -m jira_ticket_updater.main <issue_key> <target_status> [comment]

# Or use the installed command
jira-ticket-updater <issue_key> <target_status> [comment]
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and add tests
4. Commit your changes: `git commit -am 'Add some feature'`
5. Push to the branch: `git push origin feature/your-feature-name`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGE_LOG.md](CHANGE_LOG.md) for version history and updates.

## Support

- **Issues**: [GitHub Issues](https://github.com/Pandiyarajk/jira-ticket-updater/issues)
- **Documentation**: [GitHub Wiki](https://github.com/Pandiyarajk/jira-ticket-updater/wiki)
- **Email**: pandiyarajk@live.com

## Related Projects

- [Jira REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
