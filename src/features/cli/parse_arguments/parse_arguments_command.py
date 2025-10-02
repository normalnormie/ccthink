# ABOUTME: Command for parsing CLI arguments
# ABOUTME: Defines input for argument parsing operation

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParseArgumentsCommand:
    """Command to parse command-line arguments.

    Attributes:
        argv: Command-line arguments to parse (None uses sys.argv)
    """

    argv: list[str] | None = None
