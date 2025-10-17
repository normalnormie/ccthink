# ABOUTME: Helper for formatting thinking entries for git commits
# ABOUTME: Handles ANSI code stripping and line wrapping for commit messages

from src.features.phrase_transformation.line_formatter.format_thinking_line import (
    format_thinking_line,
    strip_ansi_codes,
)


def format_entries_for_commit(entries: list[str], max_length: int) -> str:
    """Format entries for commit message.

    Args:
        entries: List of thinking entries
        max_length: Maximum line length

    Returns:
        Formatted commit message
    """
    formatted_entries = []
    for line in entries:
        clean_line = strip_ansi_codes(line)
        formatted_lines = format_thinking_line(clean_line, max_length=max_length)
        formatted_entries.append("\n".join(formatted_lines))
    return "\n\n---\n\n".join(formatted_entries)
