# ABOUTME: Ensure branch command definition
# ABOUTME: Defines command to create or switch to a git branch

from dataclasses import dataclass


@dataclass
class EnsureBranchCommand:
    """Command to ensure a git branch exists and is checked out.

    Attributes:
        branch_name: Name of the branch to ensure exists.
        verbose: Enable verbose logging.
    """

    branch_name: str
    verbose: bool = False
