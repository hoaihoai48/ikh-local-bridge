from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ikh_bridge import mcp_server


class LocalMCPServerTests(unittest.TestCase):
    def test_status_reports_local_mode_and_available_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "SKILL.md"
            skill.write_text("# Test Skill", encoding="utf-8")
            with patch.dict(os.environ, {
                "IKH_BRIDGE_WORKSPACE": str(root),
                "IKH_BRIDGE_SKILL_FILE": str(skill),
            }):
                status = mcp_server.get_bridge_status()
        self.assertTrue(status["ok"])
        self.assertEqual(status["mode"], "local_mcp_tools_no_model_api")
        self.assertTrue(status["workspace_exists"])
        self.assertTrue(status["skill_exists"])
        self.assertEqual(status["skill_bytes"], len("# Test Skill"))

    def test_skill_tool_returns_canonical_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "SKILL.md"
            skill.write_text("# Canonical iKH Skill\nMandatory content-lock gate.", encoding="utf-8")
            with patch.dict(os.environ, {
                "IKH_BRIDGE_WORKSPACE": str(root),
                "IKH_BRIDGE_SKILL_FILE": str(skill),
            }):
                result = mcp_server.get_curriculum_skill()
        self.assertTrue(result["ok"])
        self.assertIn("Mandatory content-lock gate.", result["content"])
        self.assertIn("normative workflow", result["instruction"])

    def test_workspace_tools_read_write_and_run_local_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "SKILL.md"
            skill.write_text("# Test Skill", encoding="utf-8")
            script = root / "validate.py"
            script.write_text("print('VALIDATOR_RAN')\n", encoding="utf-8")
            with patch.dict(os.environ, {
                "IKH_BRIDGE_WORKSPACE": str(root),
                "IKH_BRIDGE_SKILL_FILE": str(skill),
            }):
                written = mcp_server.write_file("lesson.md", "# Lesson\n")
                read = mcp_server.read_file("lesson.md")
                listing = mcp_server.list_files(".")
                run = mcp_server.run_command(["python3", "validate.py"], timeout_seconds=10)
        self.assertTrue(written["ok"])
        self.assertEqual(read["content"], "# Lesson\n")
        self.assertIn("lesson.md", [item["name"] for item in listing["entries"]])
        self.assertEqual(run["returncode"], 0)
        self.assertIn("VALIDATOR_RAN", run["stdout"])

    def test_workspace_tools_reject_escape_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "SKILL.md"
            skill.write_text("# Test Skill", encoding="utf-8")
            with patch.dict(os.environ, {
                "IKH_BRIDGE_WORKSPACE": str(root),
                "IKH_BRIDGE_SKILL_FILE": str(skill),
            }):
                with self.assertRaisesRegex(ValueError, "escapes configured workspace"):
                    mcp_server.write_file("../outside.md", "must not write")

    def test_missing_skill_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {
                "IKH_BRIDGE_WORKSPACE": tmp,
                "IKH_BRIDGE_SKILL_FILE": str(Path(tmp) / "missing.md"),
            }):
                with self.assertRaisesRegex(FileNotFoundError, "Skill was not found"):
                    mcp_server.get_curriculum_skill()


    def test_tools_select_only_registered_instance(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            workspace_a.mkdir()
            workspace_b.mkdir()
            skill_a = root / "skill-a.md"
            skill_b = root / "skill-b.md"
            skill_a.write_text("# Skill A", encoding="utf-8")
            skill_b.write_text("# Skill B", encoding="utf-8")
            config = root / "instances.json"
            config.write_text(json.dumps({
                "schema_version": 1,
                "instances": [
                    {"id": "python-a", "name": "Python A", "workspace": str(workspace_a),
                     "skill_file": str(skill_a), "enabled": True},
                    {"id": "python-b", "name": "Python B", "workspace": str(workspace_b),
                     "skill_file": str(skill_b), "enabled": True}
                ]
            }), encoding="utf-8")
            with patch.dict(os.environ, {"IKH_BRIDGE_INSTANCES_CONFIG": str(config)}):
                status_a = mcp_server.get_bridge_status("python-a")
                status_b = mcp_server.get_bridge_status("python-b")
                written = mcp_server.write_file("only-a.md", "A", "python-a")
                with self.assertRaisesRegex(ValueError, "Unknown Bridge instance"):
                    mcp_server.read_file("only-a.md", "not-registered")
            self.assertEqual(status_a["workspace"], str(workspace_a.resolve()))
            self.assertEqual(status_b["workspace"], str(workspace_b.resolve()))
            self.assertTrue((workspace_a / "only-a.md").is_file())
            self.assertFalse((workspace_b / "only-a.md").exists())

if __name__ == "__main__":
    unittest.main()
