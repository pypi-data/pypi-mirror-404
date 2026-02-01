"""Development server for PyStator UI."""

import os
import subprocess
import sys
from pathlib import Path


def get_ui_root() -> Path:
    return Path(__file__).parent


def run_dev(api_url: str | None = None, port: int = 3000) -> None:
    ui_root = get_ui_root()
    if not (ui_root / "package.json").exists():
        print("package.json not found", file=sys.stderr)
        sys.exit(1)
    api_url = api_url or os.getenv("PYSTATOR_API_URL", "http://localhost:8000")
    env = os.environ.copy()
    env["NEXT_PUBLIC_API_URL"] = api_url
    env["PORT"] = str(port)
    if not (ui_root / "node_modules").exists():
        subprocess.run(["npm", "install"], cwd=str(ui_root), check=True)
    print(f"UI: http://localhost:{port}")
    print(f"API: {api_url}")
    subprocess.run(["npm", "run", "dev"], cwd=str(ui_root), env=env)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--api-url", default=None)
    p.add_argument("--port", type=int, default=3000)
    args = p.parse_args()
    run_dev(api_url=args.api_url, port=args.port)
