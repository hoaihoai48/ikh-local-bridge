"""CLI entrypoint."""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the iKH Local Bridge on loopback")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port (default: 8765)")
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("Only loopback hosts are allowed in this MVP")
    import uvicorn
    uvicorn.run("ikh_bridge.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
