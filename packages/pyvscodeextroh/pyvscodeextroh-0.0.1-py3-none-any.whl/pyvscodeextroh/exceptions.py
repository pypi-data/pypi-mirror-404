"""Custom package exceptions."""

class VSCodeNotFoundError(Exception):
    """Raised when the VS Code CLI ('code') cannot be found on the system."""
    pass


class VSCodeCommandError(Exception):
    """Raised when a VS Code CLI command fails."""
    pass


class PolicyError(Exception):
    """Raised when the extension policy file is missing, invalid, or unreadable."""
    pass
