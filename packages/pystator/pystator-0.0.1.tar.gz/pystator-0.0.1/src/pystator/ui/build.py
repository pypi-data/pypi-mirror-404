"""Build script for PyStator UI. Builds Next.js and copies output to static/."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_ui_root() -> Path:
    return Path(__file__).parent


def build_ui() -> int:
    ui_root = get_ui_root()
    if not (ui_root / "package.json").exists():
        print("package.json not found", file=sys.stderr)
        return 1
    if not (ui_root / "node_modules").exists():
        print("Running npm install...", file=sys.stderr)
        subprocess.run(["npm", "install"], cwd=str(ui_root), check=True)
    env = os.environ.copy()
    env["NODE_ENV"] = "production"
    subprocess.run(["npm", "run", "build"], cwd=str(ui_root), check=True, env=env)
    out = ui_root / "out"
    if not out.exists():
        print("Build output not found", file=sys.stderr)
        return 1
    static = ui_root / "static"
    if static.exists():
        shutil.rmtree(static)
    shutil.copytree(out, static)
    print(f"✓ UI built: {static}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(build_ui())
