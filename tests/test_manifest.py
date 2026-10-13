from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ikh_bridge.manifest import ManifestError, load_skill


class ManifestTests(unittest.TestCase):
    def make_skill(self, root: Path, manifest: dict) -> Path:
        folder = root / manifest.get("slug", "test-skill")
        folder.mkdir()
        (folder / "SKILL.md").write_text("# Test\n", encoding="utf-8")
        (folder / "scripts").mkdir()
        (folder / "scripts" / "check.py").write_text("print('ok')\n", encoding="utf-8")
        (folder / "skill.json").write_text(json.dumps(manifest), encoding="utf-8")
        return folder

    def test_load_valid_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {
                "schema_version": 1, "slug": "test-skill", "name": "Test",
                "version": "0.1.0", "description": "test",
                "tools": [{"id": "check", "description": "check", "entrypoint": "scripts/check.py"}],
            }
            skill = load_skill(self.make_skill(root, manifest))
            self.assertEqual(skill.slug, "test-skill")
            self.assertEqual(skill.tools[0].id, "check")

    def test_reject_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {
                "schema_version": 1, "slug": "test-skill", "name": "Test",
                "tools": [{"id": "bad", "entrypoint": "../outside.py"}],
            }
            with self.assertRaises(ManifestError):
                load_skill(self.make_skill(root, manifest))

    def test_skill_without_manifest_is_discoverable_not_runnable(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "legacy"
            folder.mkdir()
            (folder / "SKILL.md").write_text("# Legacy", encoding="utf-8")
            skill = load_skill(folder)
            self.assertEqual(skill.tools, ())
            self.assertTrue(skill.has_instructions)


if __name__ == "__main__":
    unittest.main()
