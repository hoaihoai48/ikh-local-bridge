from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from ikh_bridge import agent
from ikh_bridge.app import app
from ikh_bridge.local_tools import execute_tool


class LocalToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root / "nested").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_write_and_read_workspace_file(self):
        written = execute_tool("write_file", {"path": "nested/a.txt", "content": "hello"}, self.root)
        self.assertTrue(written["ok"])
        read = execute_tool("read_file", {"path": "nested/a.txt"}, self.root)
        self.assertEqual(read["content"], "hello")

    def test_reject_path_traversal(self):
        outside = self.root.parent / "outside-bridge-test.txt"
        try:
            with self.assertRaises(ValueError):
                execute_tool("write_file", {"path": "../outside-bridge-test.txt", "content": "bad"}, self.root)
            self.assertFalse(outside.exists())
        finally:
            if outside.exists():
                outside.unlink()

    def test_run_command_uses_workspace_and_returns_exit_code(self):
        result = execute_tool("run_command", {
            "argv": ["python", "-c", "print('ok')"], "timeout_seconds": 10
        }, self.root)
        self.assertTrue(result["ok"])
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("ok", result["stdout"])

    def test_reject_shell_string(self):
        with self.assertRaises(ValueError):
            execute_tool("run_command", {"argv": "echo ok"}, self.root)


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.skill = self.root / "SKILL.md"
        self.skill.write_text("# Test Skill\nCreate a file when asked.", encoding="utf-8")
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    @patch("ikh_bridge.agent._call_model")
    def test_agent_loads_skill_calls_local_tool_then_finishes(self, call_model):
        call_model.side_effect = [
            {
                "content": "",
                "tool_calls": [{
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "write_file",
                        "arguments": json.dumps({"path": "result.txt", "content": "done"})
                    }
                }]
            },
            {"content": "Created result.txt and verified the write tool result."}
        ]
        result = agent.run_agent(self.skill, self.workspace, "Create result.txt")
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual((self.workspace / "result.txt").read_text(encoding="utf-8"), "done")
        self.assertEqual(result["rounds"], 2)
        self.assertEqual(call_model.call_count, 2)
        first_messages = call_model.call_args_list[0].args[0]
        self.assertIn("# Test Skill", first_messages[0]["content"])

    def test_agent_requires_real_skill_file(self):
        with self.assertRaises(agent.AgentError):
            agent.run_agent(self.root / "missing.md", self.workspace, "Do work")


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.skill = self.root / "SKILL.md"
        self.skill.write_text("# Single Skill", encoding="utf-8")
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        os.environ["IKH_BRIDGE_SKILL_FILE"] = str(self.skill)
        os.environ["IKH_BRIDGE_WORKSPACE"] = str(self.workspace)
        os.environ["IKH_BRIDGE_DB"] = str(self.root / "jobs.sqlite3")
        self.client = TestClient(app)

    def tearDown(self):
        for key in ("IKH_BRIDGE_SKILL_FILE", "IKH_BRIDGE_WORKSPACE", "IKH_BRIDGE_DB"):
            os.environ.pop(key, None)
        self.temp.cleanup()

    def test_status_is_one_skill_not_a_catalog(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["execution_mode"], "single_skill_local_agent")
        self.assertTrue(data["skill_exists"])
        self.assertTrue(data["workspace_exists"])
        self.assertNotIn("skills", data)

    @patch("ikh_bridge.app.run_agent")
    def test_task_uses_configured_skill_and_workspace(self, run_agent):
        run_agent.return_value = {
            "status": "COMPLETED", "answer": "done", "rounds": 1, "transcript": [],
            "model": "test-model", "endpoint": "http://127.0.0.1:11434/v1",
            "workspace": str(self.workspace),
        }
        response = self.client.post("/api/task", json={"task": "Create a file"})
        self.assertEqual(response.status_code, 200)
        run_agent.assert_called_once_with(self.skill.resolve(), self.workspace.resolve(), "Create a file")

    def test_empty_task_rejected(self):
        response = self.client.post("/api/task", json={"task": ""})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
