import json
import os
from .exceptions import PolicyError
from .utils import DEFAULT_POLICY_PATH

class PolicyEditor:
    """
    Edits the VS Code system policy file, focusing on AllowedExtensions.
    """

    def __init__(self, policy_file=None):
        self.policy_file = policy_file or DEFAULT_POLICY_PATH

        directory = os.path.dirname(self.policy_file)
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            raise PolicyError(f"Failed to create policy directory: {e}")

        if os.path.exists(self.policy_file):
            try:
                with open(self.policy_file, "r") as f:
                    self.data = json.load(f)
            except Exception as e:
                raise PolicyError(f"Failed to read existing policy: {e}")
        else:
            self.data = {}

        if "AllowedExtensions" not in self.data or not isinstance(self.data["AllowedExtensions"], dict):
            self.data["AllowedExtensions"] = {}

    @property
    def allowed_extensions(self):
        return self.data["AllowedExtensions"]
    # Write to policy file.
    def save(self):
        """Write to policy file."""

        try:
            with open(self.policy_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except PermissionError:
            raise PolicyError("Permission denied: need root privileges to modify system policy")
        except Exception as e:
            raise PolicyError(f"Failed to write policy: {e}")

    # -----------------------------
    # Publisher helpers
    # -----------------------------

    def allow_publisher(self, publisher: str):
        """Add publisher to allow list."""

        self.allowed_extensions[publisher] = True
        self.save()

    def deny_publisher(self, publisher: str):
        """Disable publisher in allow list."""

        self.allowed_extensions[publisher] = False
        self.save()

    def remove_publisher(self, publisher: str):
        """Remove publisher from allow list."""

        if publisher in self.allowed_extensions:
            del self.allowed_extensions[publisher]
            self.save()

    # -----------------------------
    # Extension ID helpers
    # -----------------------------

    def allow_extension(self, ext_id: str):
        """Add extension to allow list."""

        self.allowed_extensions[ext_id] = True
        self.save()

    def deny_extension(self, ext_id: str):
        """Disable extension on allow list."""

        self.allowed_extensions[ext_id] = False
        self.save()

    def remove_extension(self, ext_id: str):
        """Remove extension from allow list."""

        if ext_id in self.allowed_extensions:
            del self.allowed_extensions[ext_id]
            self.save()
