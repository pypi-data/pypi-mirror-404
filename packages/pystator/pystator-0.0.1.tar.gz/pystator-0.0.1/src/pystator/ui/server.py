"""
Standalone UI server for PyStator.

Serves the built Next.js static files and proxies API requests to the PyStator API.
"""

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import httpx
    from fastapi import FastAPI, Request, Response
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except ImportError:
    httpx = FastAPI = Request = Response = FileResponse = StaticFiles = uvicorn = None


def find_ui_static_files() -> Optional[Path]:
    """Find UI static files (package or source)."""
    try:
        import pystator
        pkg = Path(pystator.__file__).parent
        static = pkg / "ui" / "static"
        if static.exists() and (static / "index.html").exists():
            return static
    except (ImportError, AttributeError):
        pass
    for p in [
        Path(__file__).parent / "static",
        Path(__file__).parent / "out",
        Path.cwd() / "src" / "pystator" / "ui" / "static",
    ]:
        if p.exists() and (p / "index.html").exists():
            return p
    return None


def get_static_dir() -> Path:
    static = find_ui_static_files()
    if static:
        return static
    raise FileNotFoundError(
        "No built UI found. Build with: pystator ui build\n"
        "Or run in dev: pystator ui dev"
    )


def create_app(api_url: str) -> "FastAPI":
    if FastAPI is None:
        raise ImportError("Install with: pip install pystator[api]")
    app = FastAPI(title="PyStator UI")
    static_dir = get_static_dir()
    _next = static_dir / "_next"
    if _next.exists():
        app.mount("/_next", StaticFiles(directory=str(_next.resolve()), html=False), name="next")
    static_assets = static_dir / "static"
    if static_assets.exists() and static_assets != _next:
        app.mount("/static", StaticFiles(directory=str(static_assets), html=False), name="static")

    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    async def proxy_api(request: Request, path: str):
        url = f"{api_url.rstrip('/')}/api/{path}"
        if request.url.query:
            url = f"{url}?{request.url.query}"
        body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "connection", "content-length")}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.request(request.method, url, headers=headers, content=body, timeout=30.0)
                return Response(content=r.content, status_code=r.status_code, headers=dict(r.headers), media_type=r.headers.get("content-type"))
            except httpx.RequestError as e:
                return Response(content=f"API request failed: {e}", status_code=502, media_type="text/plain")

    @app.get("/health")
    async def proxy_health():
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(f"{api_url.rstrip('/')}/health", timeout=5.0)
                return Response(content=r.content, status_code=r.status_code, media_type="application/json")
            except httpx.RequestError:
                return Response(content='{"status": "api_unavailable"}', status_code=503, media_type="application/json")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        if path.startswith(("api/", "_next/", "static/")):
            return Response(content="Not found", status_code=404)
        fp = static_dir / path
        if fp.exists() and fp.is_file():
            return FileResponse(str(fp))
        index = static_dir / "index.html"
        return FileResponse(str(index)) if index.exists() else Response(content="UI not built.", status_code=404, media_type="text/plain")

    return app


def serve_ui(api_url: Optional[str] = None, host: str = "127.0.0.1", port: int = 3000) -> None:
    if uvicorn is None:
        print("Install with: pip install pystator[api]", file=sys.stderr)
        sys.exit(1)
    api_url = api_url or os.getenv("PYSTATOR_API_URL", "http://localhost:8000")
    try:
        print(f"✓ UI static files: {get_static_dir()}")
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    app = create_app(api_url)
    print(f"PyStator UI: http://{host}:{port}")
    print(f"API: {api_url}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--api-url", default=None)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=3000)
    args = p.parse_args()
    serve_ui(api_url=args.api_url, host=args.host, port=args.port)
