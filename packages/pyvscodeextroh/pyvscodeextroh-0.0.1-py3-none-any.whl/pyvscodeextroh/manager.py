import subprocess
from .exceptions import VSCodeNotFoundError, VSCodeCommandError
from .policy import ExtensionPolicy


class VSCodeExtensionManager:
    """Manage VSCode extensions"""

    def __init__(self, code_path="code"):
        self.code_path = code_path
        if not self._is_code_available():
            raise VSCodeNotFoundError("VS Code CLI ('code') not found in PATH.")

    def _is_code_available(self):
        """Check if VSCode is installed."""

        try:
            subprocess.run([self.code_path, "--version"], capture_output=True)
            return True
        except FileNotFoundError:
            return False

    def _run(self, args):
        """Run VSCode cli commands."""

        cmd = [self.code_path] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise VSCodeCommandError(e.stderr.strip())

    # -----------------------------
    # Public API
    # -----------------------------

    def list_extensions(self):
        """List installed extensions."""

        output = self._run(["--list-extensions"])
        return output.splitlines()

    def list_with_versions(self):
        """List installed extensions with versions."""

        output = self._run(["--list-extensions", "--show-versions"])
        return output.splitlines()

    def install_extension(self, extension_id:str):
        """Install specified extension."""

        self._run(["--install-extension", extension_id])
        return f"Installed: {extension_id}"

    def uninstall_extension(self, extension_id: str):
        """Uninstall specified extension."""

        self._run(["--uninstall-extension", extension_id])
        return f"Uninstalled: {extension_id}"


class VSCodePolicyManager:
    """
    Enforces the AllowedExtensions policy:

    - Allowed if:
        * extension ID explicitly allowed, or
        * publisher explicitly allowed.
    - Disallowed otherwise → uninstall.
    """

    def __init__(self, policy_file=None, code_path="code"):
        self.policy = ExtensionPolicy(policy_file)
        self.manager = VSCodeExtensionManager(code_path)

    def _get_publisher(self, ext_id: str) -> str:
        """Get specified publisher."""

        return ext_id.split(".", 1)[0]

    def get_disallowed(self):
        """Get disallowed extensions."""

        installed = set(self.manager.list_extensions())
        disallowed = set()

        for ext in installed:
            if not self.policy.is_extension_allowed(ext):
                disallowed.add(ext)

        return disallowed

    def enforce_policy(self):
        """Enforce policy. Uninstalls disallowed extensions."""
        
        removed = []

        for ext in self.get_disallowed():
            self.manager.uninstall_extension(ext)
            removed.append(ext)

        return {
            "removed": removed,
            "installed": []
        }
