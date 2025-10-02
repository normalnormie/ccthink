# ABOUTME: Merge branch command definition
# ABOUTME: Defines command to merge a branch into another branch

from dataclasses import dataclass


@dataclass
class MergeBranchCommand:
    """Command to merge a branch into target branch.

    Attributes:
        source_branch: Branch to merge from.
        target_branch: Branch to merge into.
        quit_on_conflict: Quit if merge conflict occurs.
        verbose: Enable verbose logging.
    """

    source_branch: str
    target_branch: str
    quit_on_conflict: bool = False
    verbose: bool = False
