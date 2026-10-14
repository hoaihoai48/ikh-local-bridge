from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ikh_bridge.instances import InstanceConfigError, get_instance, load_instances


class InstanceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace_a = self.root / "workspace-a"
        self.workspace_b = self.root / "workspace-b"
        self.workspace_a.mkdir()
        self.workspace_b.mkdir()
        self.skill_a = self.root / "skill-a.md"
        self.skill_b = self.root / "skill-b.md"
        self.skill_a.write_text("# Skill A", encoding="utf-8")
        self.skill_b.write_text("# Skill B", encoding="utf-8")
        self.config = self.root / "instances.json"
        self.config.write_text(json.dumps({
            "schema_version": 1,
            "instances": [
                {"id": "python-a", "name": "Python A", "workspace": str(self.workspace_a),
                 "skill_file": str(self.skill_a), "enabled": True},
                {"id": "python-b", "name": "Python B", "workspace": str(self.workspace_b),
                 "skill_file": str(self.skill_b), "enabled": True},
                {"id": "disabled", "name": "Disabled", "workspace": str(self.workspace_b),
                 "skill_file": str(self.skill_b), "enabled": False}
            ]
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_registry_resolves_separate_instances(self):
        items = load_instances(self.config)
        self.assertEqual(items["python-a"].workspace, self.workspace_a.resolve())
        self.assertEqual(items["python-b"].workspace, self.workspace_b.resolve())
        self.assertNotEqual(items["python-a"].skill_file, items["python-b"].skill_file)

    def test_unknown_and_disabled_instances_fail_closed(self):
        with patch.dict(os.environ, {"IKH_BRIDGE_INSTANCES_CONFIG": str(self.config)}):
            with self.assertRaisesRegex(InstanceConfigError, "Unknown Bridge instance"):
                get_instance("not-registered")
            with self.assertRaisesRegex(InstanceConfigError, "disabled"):
                get_instance("disabled")

    def test_duplicate_instance_ids_rejected(self):
        data = json.loads(self.config.read_text(encoding="utf-8"))
        data["instances"].append(data["instances"][0])
        self.config.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(InstanceConfigError, "duplicate instance id"):
            load_instances(self.config)

    def test_missing_workspace_rejected(self):
        data = json.loads(self.config.read_text(encoding="utf-8"))
        data["instances"][0]["workspace"] = str(self.root / "missing")
        self.config.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(InstanceConfigError, "directory does not exist"):
            load_instances(self.config)


if __name__ == "__main__":
    unittest.main()
