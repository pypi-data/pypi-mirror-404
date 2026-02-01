import unittest
from unittest.mock import patch
import tempfile
import json
import os

from src.pyvscodeextroh import VSCodePolicyManager

class TestVSCodePolicyManager(unittest.TestCase):

    @patch("src.pyvscodeextroh.manager.VSCodeExtensionManager")
    def test_enforce_policy(self, MockManager):
        # Mock VSCodeExtensionManager instance
        instance = MockManager.return_value

        # Simulate installed extensions
        instance.list_extensions.return_value = [
            "microsoft.goodext",
            "evilcorp.badext",
            "github.cooltool"
        ]

        instance.uninstall_extension.return_value = None

        # Create temporary policy file
        with tempfile.TemporaryDirectory() as tmp:
            policy_path = os.path.join(tmp, "policy.json")

            # Allowed publishers + allowed extension ID
            data = {
                "AllowedExtensions": {
                    "microsoft": True,
                    "github": True,
                    "microsoft.goodext": True
                }
            }

            with open(policy_path, "w") as f:
                json.dump(data, f)

            pm = VSCodePolicyManager(policy_path)
            result = pm.enforce_policy()

            # evilcorp.badext should be removed
            instance.uninstall_extension.assert_called_with("evilcorp.badext")

            # Check results
            self.assertIn("evilcorp.badext", result["removed"])
            self.assertEqual(result["installed"], [])  # no installs in this policy model
