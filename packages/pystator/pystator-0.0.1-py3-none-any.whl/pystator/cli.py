"""CLI for PyStator: api and ui subcommands."""

import argparse
import importlib.util
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PyStator - FSM library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command", required=True)

    api_parser = subparsers.add_parser("api", help="Start the API server")
    api_parser.add_argument("--host", type=str, default="0.0.0.0")
    api_parser.add_argument("--port", type=int, default=8000)
    api_parser.add_argument("--reload", action="store_true", default=True)
    api_parser.add_argument("--no-reload", dest="reload", action="store_false")

    ui_parser = subparsers.add_parser("ui", help="UI commands")
    ui_sub = ui_parser.add_subparsers(dest="ui_command", required=True)
    ui_serve = ui_sub.add_parser("serve", help="Serve built UI")
    ui_serve.add_argument("--api-url", type=str, default=None)
    ui_serve.add_argument("--host", type=str, default="127.0.0.1")
    ui_serve.add_argument("--port", type=int, default=3000)
    ui_dev = ui_sub.add_parser("dev", help="Run UI dev server")
    ui_dev.add_argument("--api-url", type=str, default=None)
    ui_dev.add_argument("--port", type=int, default=3000)
    ui_build = ui_sub.add_parser("build", help="Build UI for production")

    args = parser.parse_args()

    if args.command == "api":
        try:
            import uvicorn
        except ImportError:
            print("Install with: pip install pystator[api]", file=sys.stderr)
            return 1
        uvicorn.run(
            "pystator.api.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
        return 0

    if args.command == "ui":
        try:
            import pystator
            ui_path = Path(pystator.__file__).parent / "ui"
        except (ImportError, AttributeError):
            ui_path = Path(__file__).parent / "ui"
        if not ui_path.exists():
            print("UI not found", file=sys.stderr)
            return 1

        if args.ui_command == "serve":
            spec = importlib.util.spec_from_file_location("server", ui_path / "server.py")
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.serve_ui(
                    api_url=args.api_url or os.getenv("PYSTATOR_API_URL"),
                    host=args.host,
                    port=args.port,
                )
            return 0
        if args.ui_command == "dev":
            spec = importlib.util.spec_from_file_location("dev", ui_path / "dev.py")
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.run_dev(api_url=args.api_url or os.getenv("PYSTATOR_API_URL"), port=args.port)
            return 0
        if args.ui_command == "build":
            spec = importlib.util.spec_from_file_location("build", ui_path / "build.py")
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod.build_ui()
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
