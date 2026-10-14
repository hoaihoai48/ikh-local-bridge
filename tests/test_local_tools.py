from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from ikh_bridge.local_tools import TOOL_DEFINITIONS, execute_tool

class LocalToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def test_list_and_read_file(self):
        (self.root / "notes.md").write_text("hello", encoding="utf-8")
        listing = execute_tool("list_files", {}, self.root)
        self.assertTrue(listing["ok"])
        self.assertIn("notes.md", [x["name"] for x in listing["entries"]])
        self.assertEqual(execute_tool("read_file", {"path":"notes.md"}, self.root)["content"], "hello")
    def test_write_file_reports_whether_it_overwrote(self):
        first = execute_tool("write_file", {"path":"nested/out.md","content":"one"}, self.root)
        second = execute_tool("write_file", {"path":"nested/out.md","content":"two"}, self.root)
        self.assertFalse(first["overwrote_existing_file"])
        self.assertTrue(second["overwrote_existing_file"])
        self.assertEqual((self.root/"nested/out.md").read_text(encoding="utf-8"), "two")
    def test_blocks_path_traversal_and_secrets(self):
        with self.assertRaises(ValueError):
            execute_tool("read_file", {"path":"../outside.txt"}, self.root)
        (self.root/".env").write_text("secret", encoding="utf-8")
        with self.assertRaises(ValueError):
            execute_tool("read_file", {"path":".env"}, self.root)
    def test_command_is_argv_only_and_allowlisted(self):
        with self.assertRaises(ValueError):
            execute_tool("run_command", {"argv":["sh","-c","echo unsafe"]}, self.root)
    def test_command_rejects_executable_paths_even_if_basename_is_allowlisted(self):
        # A basename-only allowlist would permit /tmp/python or another
        # arbitrary executable to masquerade as an approved interpreter.
        for executable in ("/tmp/python", "./python3", "/usr/bin/git"):
            with self.subTest(executable=executable):
                with self.assertRaisesRegex(ValueError, "command name without a path"):
                    execute_tool("run_command", {"argv": [executable, "--version"]}, self.root)

    def test_git_read_only_commands_reject_write_and_external_helper_options(self):
        for argv in (
            ["git", "diff", "--output=../outside.txt"],
            ["git", "diff", "--ext-diff"],
            ["git", "show", "--textconv"],
            ["git", "status", "--work-tree=../outside"],
        ):
            with self.subTest(argv=argv):
                with self.assertRaisesRegex(ValueError, "git option may write outside"):
                    execute_tool("run_command", {"argv": argv}, self.root)

    def test_symlink_to_outside_workspace_is_blocked_for_read_and_write(self):
        outside = self.root.parent / (self.root.name + "-outside.txt")
        outside.write_text("do not touch", encoding="utf-8")
        link = self.root / "outside-link.txt"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            outside.unlink(missing_ok=True)
            self.skipTest("symlinks are not available in this environment")
        try:
            with self.assertRaises(ValueError):
                execute_tool("read_file", {"path": "outside-link.txt"}, self.root)
            with self.assertRaises(ValueError):
                execute_tool("write_file", {"path": "outside-link.txt", "content": "modified"}, self.root)
            self.assertEqual(outside.read_text(encoding="utf-8"), "do not touch")
        finally:
            outside.unlink(missing_ok=True)

    def test_write_blocks_protected_runtime_paths(self):
        for path in (".git/should-not-exist", ".config/secret", ".env.local"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    execute_tool("write_file", {"path": path, "content": "no"}, self.root)

    def test_write_blocks_path_traversal_and_oversized_content(self):
        with self.assertRaises(ValueError):
            execute_tool("write_file", {"path": "../outside.txt", "content": "no"}, self.root)
        with self.assertRaises(ValueError):
            execute_tool("write_file", {"path": "large.md", "content": "x" * (220_000 + 1)}, self.root)
        self.assertFalse((self.root.parent / "outside.txt").exists())

    def test_fetch_url_rejects_http_and_local_hosts(self):
        with self.assertRaises(ValueError):
            execute_tool("fetch_url", {"url":"http://example.com"}, self.root)
        with self.assertRaises(ValueError):
            execute_tool("fetch_url", {"url":"https://127.0.0.1"}, self.root)
    def test_image_generation_is_not_a_bridge_tool(self):
        tool_names = [item["function"]["name"] for item in TOOL_DEFINITIONS]
        self.assertNotIn("generate_image", tool_names)
        result = execute_tool("generate_image", {"prompt": "test", "output_path": "test.png"}, self.root)
        self.assertFalse(result["ok"])
        self.assertIn("Unknown tool", result["error"])

    def test_runs_python_script_without_shell(self):
        (self.root/"check.py").write_text("print('LOCAL_TOOL_PASS')\n", encoding="utf-8")
        result = execute_tool("run_command", {"argv":["python3","check.py"],"timeout_seconds":10}, self.root)
        self.assertEqual(result["returncode"], 0)
        self.assertIn("LOCAL_TOOL_PASS", result["stdout"])

if __name__ == "__main__":
    unittest.main()
