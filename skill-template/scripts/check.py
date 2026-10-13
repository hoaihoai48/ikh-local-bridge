"""Non-destructive example tool used to smoke-test a generated Skill."""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the Skill workspace path")
    parser.add_argument("--workspace", help="Optional workspace path to inspect")
    args = parser.parse_args()
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd().resolve()
    if not workspace.is_dir():
        parser.error("workspace must be an existing directory")
    print(json.dumps({
        "status": "ok",
        "workspace": str(workspace),
        "entries": len(list(workspace.iterdir())),
        "note": "Metadata only; no files were changed."
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
