"""Jira Ticket Updater v1.0.1 - Main entry point for the CLI application."""

import sys

from .cli_handlers import parse_arguments, process_issue_operation


def main():
    """Main entry point for the jira-ticket-updater v1.0.0 command-line tool."""
    parsed_args = parse_arguments(sys.argv[1:])
    if parsed_args is None:
        sys.exit(1)

    success = process_issue_operation(parsed_args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()