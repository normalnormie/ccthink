# ABOUTME: Commit thinking command definition
# ABOUTME: Defines command to create a git commit from thinking content

from dataclasses import dataclass


@dataclass
class CommitThinkingCommand:
    """Command to commit thinking entries as git commit.

    Attributes:
        message: Commit message containing thinking content.
        simulate: Simulate without actually committing.
        verbose: Enable verbose logging.
    """

    message: str
    simulate: bool = False
    verbose: bool = False
