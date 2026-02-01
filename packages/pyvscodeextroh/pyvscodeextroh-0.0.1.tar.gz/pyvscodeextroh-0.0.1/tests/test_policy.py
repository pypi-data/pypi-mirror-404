import unittest
import tempfile
import json
import os

from src.pyvscodeextroh import ExtensionPolicy
from src.pyvscodeextroh import PolicyError

class TestExtensionPolicy(unittest.TestCase):

    def test_load_valid_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "policy.json")

            data = {
                "AllowedExtensions": {
                    "microsoft": True,
                    "github": True,
                    "microsoft.testext": True
                }
            }

            with open(path, "w") as f:
                json.dump(data, f)

            policy = ExtensionPolicy(path)

            # Publisher allowed
            self.assertTrue(policy.is_publisher_allowed("microsoft"))
            self.assertTrue(policy.is_publisher_allowed("github"))

            # Extension ID allowed
            self.assertTrue(policy.is_extension_allowed("microsoft.testext"))

            # Disallowed extension
            self.assertFalse(policy.is_extension_allowed("evilcorp.badext"))

    def test_missing_policy_file_creates_new(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "policy.json")

            policy = ExtensionPolicy(path)

            # File should now exist
            self.assertTrue(os.path.exists(path))

            # Should contain AllowedExtensions dict
            self.assertIn("AllowedExtensions", policy.raw)
            self.assertEqual(policy.allowed_extensions, {})

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "policy.json")

            with open(path, "w") as f:
                f.write("{invalid json}")

            with self.assertRaises(PolicyError):
                ExtensionPolicy(path)
