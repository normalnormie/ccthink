# ABOUTME: Handler for parsing CLI arguments
# ABOUTME: Implements argument parsing logic using argparse

from __future__ import annotations

import argparse

from src.features.cli.parse_arguments.parse_arguments_command import (
    ParseArgumentsCommand,  # noqa: TC001
)
from src.features.cli.parse_arguments.parse_arguments_response import (
    ParseArgumentsResponse,
)


class ParseArgumentsHandler:
    """Handler for parsing command-line arguments."""

    @staticmethod
    def handle(command: ParseArgumentsCommand) -> ParseArgumentsResponse:
        """Parse command-line arguments.

        Args:
            command: Command containing arguments to parse

        Returns:
            Response containing parsed argument values
        """
        parser = argparse.ArgumentParser(
            prog="ccthink",
            description="Monitor Claude Code thinking sessions in real-time",
            epilog="Settings persist to ccthink.conf and are remembered across sessions.",
        )

        # Git commit operations
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Enable git commits for thinking entries (creates conversation-specific branches)",
        )
        parser.add_argument(
            "--no-commit",
            action="store_true",
            help="Disable git commits (display only mode)",
        )

        # Sonnet compression
        parser.add_argument(
            "--sonnet",
            action="store_true",
            help="Enable Sonnet phrase compression with sentiment colors (uses Claude Code auth, no API key needed)",
        )
        parser.add_argument(
            "--no-sonnet",
            action="store_true",
            help="Disable Sonnet phrase compression (show raw thinking)",
        )

        # Streaming output
        parser.add_argument(
            "--streaming",
            action="store_true",
            help="Enable streaming output for Sonnet compression (token-by-token display)",
        )
        parser.add_argument(
            "--no-streaming",
            action="store_true",
            help="Disable streaming output (show complete compressed result instantly)",
        )

        # Colored output
        parser.add_argument(
            "--colors",
            action="store_true",
            help="Enable ANSI 256 sentiment-based colors for compressed phrases",
        )
        parser.add_argument(
            "--no-colors",
            action="store_true",
            help="Disable colored output (plain text only)",
        )

        # Verbose logging
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging with timestamps (all output goes through logger)",
        )
        parser.add_argument(
            "--no-verbose",
            action="store_true",
            help="Disable verbose logging (standard output mode)",
        )

        # Simulate mode
        parser.add_argument(
            "--simulate",
            action="store_true",
            help="Enable dry-run mode (skip actual git operations, useful for testing)",
        )
        parser.add_argument(
            "--no-simulate",
            action="store_true",
            help="Disable dry-run mode (perform actual git operations)",
        )

        args = parser.parse_args(command.argv)

        return ParseArgumentsResponse(
            enable_commit=args.commit or None,
            disable_commit=args.no_commit or None,
            enable_sonnet=args.sonnet or None,
            disable_sonnet=args.no_sonnet or None,
            enable_streaming=args.streaming or None,
            disable_streaming=args.no_streaming or None,
            enable_colors=args.colors or None,
            disable_colors=args.no_colors or None,
            enable_verbose=args.verbose or None,
            disable_verbose=args.no_verbose or None,
            enable_simulate=args.simulate or None,
            disable_simulate=args.no_simulate or None,
        )
