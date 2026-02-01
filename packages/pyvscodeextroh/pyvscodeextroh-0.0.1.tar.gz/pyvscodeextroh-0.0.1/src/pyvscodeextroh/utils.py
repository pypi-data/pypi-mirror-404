# Default policy file.
DEFAULT_POLICY_PATH = "/etc/vscode/policy.json"

def is_installed(ext_id: str, installed_list: list):
    """Simple helper that checks whether an extension ID is in a list."""

    return ext_id in installed_list
