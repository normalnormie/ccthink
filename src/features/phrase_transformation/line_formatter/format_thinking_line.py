# ABOUTME: Smart line formatter for thinking text with natural breakpoint detection
# ABOUTME: Splits long lines at punctuation (. ; :) to maintain 50-75 character target

import re
from collections.abc import Sequence

# ANSI color code regex
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI color codes from text.

    Args:
        text: Text potentially containing ANSI codes

    Returns:
        Plain text without ANSI codes
    """
    return ANSI_PATTERN.sub("", text)


def extract_ansi_color(text: str) -> str | None:
    r"""Extract the ANSI color code from colored text.

    Args:
        text: Text potentially containing ANSI color codes

    Returns:
        The color code (e.g., "\x1b[38;5;34m") or None if no color found
    """
    match = re.search(r"\x1b\[38;5;(\d+)m", text)
    if match:
        return match.group(0)
    return None


def apply_ansi_color(text: str, color_code: str) -> str:
    r"""Apply ANSI color code to text.

    Args:
        text: Plain text to colorize
        color_code: ANSI color code (e.g., "\x1b[38;5;34m")

    Returns:
        Colorized text with reset code at end
    """
    return f"{color_code}{text}\x1b[0m"


def format_thinking_line(
    text: str,
    min_line_length: int = 30,
    target_length: int = 55,
    max_length: int = 55,
) -> list[str]:
    """Split long thinking text into readable lines at natural breakpoints.

    Intelligently splits text at natural pauses (period, semicolon, colon, comma) to
    create lines suitable for quick scanning. Aims for ~55 character lines
    while preventing any line from exceeding max_length characters.

    Args:
        text: The text to format
        min_line_length: Minimum acceptable line length (default: 30)
        target_length: Preferred line length to aim for (default: 55)
        max_length: Hard maximum line length (default: 55, overridden by config)

    Returns:
        List of formatted lines, split at natural breakpoints

    Example:
        >>> format_thinking_line(
        ...     "Clearing todo list—implementation complete, "
        ...     "awaiting manual testing by Ralph"
        ... )
        [
            "Clearing todo list—implementation complete,",
            "awaiting manual testing by Ralph"
        ]
    """
    # Short enough already
    if len(text) <= target_length:
        return [text]

    lines: list[str] = []
    remaining = text

    while len(remaining) > target_length:
        split_at: int | None = None
        best_split: int | None = None
        best_distance: int | None = None

        # Try breakpoints in order of preference: period, semicolon, colon, close-paren, comma
        for separator in [". ", "; ", ": ", ") ", ", "]:
            # Find all occurrences before max_length
            pos = 0
            while pos < len(remaining):
                idx = remaining.find(separator, pos, max_length)
                if idx == -1:
                    break

                # Skip numbered list markers (e.g., "1. ", "2. ", "10. ")
                if separator == ". " and idx > 0:
                    # Check if character before ". " is a digit
                    if remaining[idx - 1].isdigit():
                        # Could be a numbered list - check if all preceding chars are digits/whitespace
                        prefix_start = idx - 1
                        while prefix_start > 0 and remaining[prefix_start - 1].isdigit():
                            prefix_start -= 1
                        # If at start or preceded by whitespace, it's a list marker
                        if prefix_start == 0 or remaining[prefix_start - 1].isspace():
                            pos = idx + 1
                            continue

                split_pos = idx + len(separator)

                # Check if this would create a valid split
                if split_pos >= min_line_length:
                    # Calculate distance from target
                    distance = abs(split_pos - target_length)

                    # Use this split if it's closer to target than previous best
                    if best_distance is None or distance < best_distance:
                        best_split = split_pos
                        best_distance = distance

                pos = idx + 1

            # If we found a good split for this separator, use it
            if best_split is not None:
                split_at = best_split
                break

        # No good breakpoint found but exceeding max_length
        if split_at is None and len(remaining) > max_length:
            # Force split at last space before max_length
            space_idx = remaining.rfind(" ", 0, max_length)
            if space_idx != -1:
                split_at = space_idx + 1
            else:
                # No space found, hard split at max_length
                split_at = max_length

        if split_at:
            # Split here and continue
            lines.append(remaining[:split_at].rstrip())
            remaining = remaining[split_at:].lstrip()
        else:
            # No split needed (line is > target but < max with no good breakpoint)
            break

    # Add remaining text
    if remaining:
        lines.append(remaining)

    return lines


def format_colored_thinking_line(text: str, max_length: int = 55) -> list[str]:
    """Format a potentially colored thinking line, preserving color across splits.

    If the text contains ANSI color codes, the color is extracted and the plain
    text is split on newlines first, then formatted, and color is reapplied to each line.
    Markdown code blocks (between ``` markers) are preserved without formatting.

    Args:
        text: Thinking line potentially containing ANSI color codes
        max_length: Maximum line length (default: 55, overridden by config)

    Returns:
        List of formatted lines with color preserved on each split
    """
    # Check if text has color codes
    color_code = extract_ansi_color(text)

    if color_code:
        # Extract color, split on newlines, format each line, then reapply color
        plain_text = strip_ansi_codes(text)
        # Split on newlines first, then format each line
        natural_lines = plain_text.split("\n")
        split_lines: list[str] = []
        in_code_block = False
        for natural_line in natural_lines:
            # Check for code block markers
            if natural_line.strip().startswith("```"):
                in_code_block = not in_code_block
                split_lines.append(natural_line)
            elif in_code_block:
                # Don't format lines inside code blocks
                split_lines.append(natural_line)
            elif natural_line:
                split_lines.extend(format_thinking_line(natural_line, max_length=max_length))
            else:
                split_lines.append("")
        return [apply_ansi_color(line, color_code) for line in split_lines]

    # No color codes, split on newlines first then format each line
    natural_lines = text.split("\n")
    result: list[str] = []
    in_code_block = False
    for natural_line in natural_lines:
        # Check for code block markers
        if natural_line.strip().startswith("```"):
            in_code_block = not in_code_block
            result.append(natural_line)
        elif in_code_block:
            # Don't format lines inside code blocks
            result.append(natural_line)
        elif natural_line:
            result.extend(format_thinking_line(natural_line, max_length=max_length))
        else:
            result.append("")
    return result


def format_thinking_lines(lines: Sequence[str], max_length: int = 55) -> list[str]:
    """Format multiple thinking lines, splitting long ones at natural breakpoints.

    First splits on existing newline characters to respect document structure,
    then applies length-based formatting to each resulting line.
    Markdown code blocks (between ``` markers) are preserved without formatting.

    Args:
        lines: Sequence of thinking lines to format
        max_length: Maximum line length (default: 55, overridden by config)

    Returns:
        List of formatted lines with long lines split appropriately
    """
    result: list[str] = []
    in_code_block = False

    for line in lines:
        # Split on existing newlines first to preserve document structure
        natural_lines = line.split("\n")

        for natural_line in natural_lines:
            # Check for code block markers
            if natural_line.strip().startswith("```"):
                in_code_block = not in_code_block
                result.append(natural_line)
            elif in_code_block:
                # Don't format lines inside code blocks
                result.append(natural_line)
            elif natural_line:  # Non-empty line
                result.extend(format_thinking_line(natural_line, max_length=max_length))
            else:  # Empty line (preserve paragraph breaks)
                result.append("")

    return result
