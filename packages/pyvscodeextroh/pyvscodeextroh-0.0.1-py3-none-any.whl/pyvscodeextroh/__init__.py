"""Manage vscode extensions."""

# Runtime guard
# Package only supported on linux
import sys
if sys.platform != "linux":
    raise RuntimeError("pyvscodeextroh is only supported on Linux.")

# Exported classes and functions
from .manager import VSCodeExtensionManager, VSCodePolicyManager
from .policy import ExtensionPolicy
from .exceptions import VSCodeNotFoundError, VSCodeCommandError, PolicyError
from .policy_editor import PolicyEditor
