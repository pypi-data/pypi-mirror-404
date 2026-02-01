import json
import os
from .exceptions import PolicyError
from .utils import DEFAULT_POLICY_PATH

class ExtensionPolicy:
    """
    Wraps the VS Code system policy file.

    Expected structure (simplified):

    {
        "AllowedExtensions": {
            "microsoft": true,
            "github": true,
            "ms-python.python": true
        },
        ...
    }
    """

    def __init__(self, policy_file=None):
        self.policy_file = policy_file or DEFAULT_POLICY_PATH

        if not os.path.exists(self.policy_file):
            # Create a minimal default policy file
            try:
                os.makedirs(os.path.dirname(self.policy_file), exist_ok=True)
                with open(self.policy_file, "w") as f:
                    json.dump({
                        "AllowedExtensions": {},
                    }, f, indent=2)
            except Exception as e:
                raise PolicyError(f"Failed to create missing policy file: {e}")

        try:
            with open(self.policy_file, "r") as f:
                data = json.load(f)
        except Exception as e:
            raise PolicyError(f"Failed to load policy file: {e}")

        self.raw = data
        self.allowed_extensions = data.get("AllowedExtensions", {}) or {}

    # -----------------------------
    # Query helpers
    # -----------------------------

    def is_publisher_allowed(self, publisher: str) -> bool:
        """Returns True if the publisher is explicitly allowed."""

        value = self.allowed_extensions.get(publisher)
        return bool(value) is True

    def is_extension_allowed(self, ext_id: str) -> bool:
        """
        Returns True if either:
        - the full extension ID is explicitly allowed, or
        - its publisher is allowed.
        """
        if ext_id in self.allowed_extensions:
            return bool(self.allowed_extensions[ext_id]) is True

        publisher = ext_id.split(".", 1)[0]
        return self.is_publisher_allowed(publisher)

    def get_allowed_publishers(self):
        """Get all allowed publishers."""

        return {
            k for k, v in self.allowed_extensions.items()
            if "." not in k and bool(v) is True
        }

    def get_allowed_extension_ids(self):
        """Get all allowed extension ids."""
        
        return {
            k for k, v in self.allowed_extensions.items()
            if "." in k and bool(v) is True
        }
