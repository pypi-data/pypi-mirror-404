import unittest
import tempfile
import json
import os

from src.pyvscodeextroh import PolicyEditor

class TestPolicyEditor(unittest.TestCase):

    def test_create_and_modify_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy_path = os.path.join(tmp, "policy.json")

            editor = PolicyEditor(policy_path)

            # Add publisher + extension
            editor.allow_publisher("microsoft")
            editor.allow_extension("microsoft.testext")

            with open(policy_path, "r") as f:
                data = json.load(f)

            # Check publisher allowed
            self.assertIn("microsoft", data["AllowedExtensions"])
            self.assertTrue(data["AllowedExtensions"]["microsoft"])

            # Check extension allowed
            self.assertIn("microsoft.testext", data["AllowedExtensions"])
            self.assertTrue(data["AllowedExtensions"]["microsoft.testext"])

            # Remove extension
            editor.remove_extension("microsoft.testext")

            with open(policy_path, "r") as f:
                data = json.load(f)

            self.assertNotIn("microsoft.testext", data["AllowedExtensions"])

    def test_directory_auto_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            nested_path = os.path.join(tmp, "deep", "nested", "policy.json")

            editor = PolicyEditor(nested_path)
            self.assertIsInstance(editor, PolicyEditor)

            # Directory should exist
            self.assertTrue(os.path.exists(os.path.dirname(nested_path)))

            # File should NOT exist yet (no save triggered)
            self.assertFalse(os.path.exists(nested_path))

            # Trigger file creation
            editor.allow_publisher("microsoft")

            # Now the file must exist
            self.assertTrue(os.path.exists(nested_path))

            # And AllowedExtensions must exist
            with open(nested_path, "r") as f:
                data = json.load(f)

            self.assertIn("AllowedExtensions", data)
            self.assertIsInstance(data["AllowedExtensions"], dict)
