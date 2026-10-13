"""Integration tests for Local Bridge FastAPI endpoints and tool execution."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from ikh_bridge.app import app
from ikh_bridge.jobs import JobStore


class BridgeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.skills_dir = Path(self.temp_dir) / "skills"
        self.skills_dir.mkdir()
        self.workspace_dir = Path(self.temp_dir) / "workspace"
        self.workspace_dir.mkdir()

        # Create a sample skill with valid manifest and check tool
        self.sample_skill = self.skills_dir / "test-sample-skill"
        self.sample_skill.mkdir()
        (self.sample_skill / "SKILL.md").write_text("# Test Skill\nDescription", encoding="utf-8")
        scripts_dir = self.sample_skill / "scripts"
        scripts_dir.mkdir()
        script_file = scripts_dir / "echo_check.py"
        script_file.write_text(
            'import os, json\n'
            'print(json.dumps({"status": "passed", "ws": os.environ.get("IKH_BRIDGE_WORKSPACE")}))\n',
            encoding="utf-8"
        )
        manifest_file = self.sample_skill / "skill.json"
        manifest_file.write_text(
            '{\n'
            '  "schema_version": 1,\n'
            '  "slug": "test-sample-skill",\n'
            '  "name": "Test Sample Skill",\n'
            '  "version": "1.0.0",\n'
            '  "description": "A test skill for bridge tests",\n'
            '  "tools": [\n'
            '    {\n'
            '      "id": "echo_check",\n'
            '      "description": "Echo check test",\n'
            '      "entrypoint": "scripts/echo_check.py",\n'
            '      "timeout_seconds": 10\n'
            '    }\n'
            '  ]\n'
            '}\n',
            encoding="utf-8"
        )

        os.environ["IKH_BRIDGE_SKILLS_DIR"] = str(self.skills_dir)
        db_path = Path(self.temp_dir) / "test_jobs.sqlite3"
        os.environ["IKH_BRIDGE_DB"] = str(db_path)
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.pop("IKH_BRIDGE_SKILLS_DIR", None)
        os.environ.pop("IKH_BRIDGE_DB", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["app"], "ikh-local-bridge")

    def test_skills_discovery_api(self):
        res = self.client.get("/api/skills")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data["skills"]), 1)
        skill = data["skills"][0]
        self.assertEqual(skill["slug"], "test-sample-skill")
        self.assertTrue(skill["runnable"])
        self.assertEqual(len(skill["tools"]), 1)
        self.assertEqual(skill["tools"][0]["id"], "echo_check")

    def test_run_tool_unreviewed_rejected(self):
        res = self.client.post("/api/run", json={
            "skill_slug": "test-sample-skill",
            "tool_id": "echo_check",
            "workspace": str(self.workspace_dir),
            "reviewed": False,
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("Review the Skill script", res.json()["detail"])

    def test_run_tool_success(self):
        res = self.client.post("/api/run", json={
            "skill_slug": "test-sample-skill",
            "tool_id": "echo_check",
            "workspace": str(self.workspace_dir),
            "reviewed": True,
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "COMPLETED")
        self.assertEqual(data["exit_code"], 0)
        self.assertIn('"status": "passed"', data["stdout"])

        # Check job history
        res_jobs = self.client.get("/api/jobs")
        self.assertEqual(res_jobs.status_code, 200)
        jobs = res_jobs.json()["jobs"]
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["status"], "COMPLETED")
        self.assertEqual(jobs[0]["skill_slug"], "test-sample-skill")
