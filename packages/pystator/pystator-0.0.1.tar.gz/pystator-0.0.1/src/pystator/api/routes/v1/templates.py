"""
FSM template routes.

FSM templates (starter YAML configs) live under pystator/data/templates/fsm/.
List and serve by filename (e.g. blank.yaml, order_management.yaml).
"""

from pathlib import Path

import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _find_fsm_template_dir() -> Path:
    """
    Find FSM template directory.

    Templates live under pystator/data/templates/fsm/.
    Priority: project root (editable install), then package-relative.
    """
    try:
        import pystator

        pkg_dir = Path(pystator.__file__).resolve().parent
        # Project root: src/pystator -> src -> project root
        project_root = pkg_dir.parent.parent
        fsm_dir = project_root / "data" / "templates" / "fsm"
        if fsm_dir.exists() and (fsm_dir / "blank.yaml").exists():
            return fsm_dir
    except (ImportError, AttributeError):
        pass

    dev_paths = [
        Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "templates" / "fsm",
        Path.cwd() / "data" / "templates" / "fsm",
    ]
    for p in dev_paths:
        if p.exists() and (p / "blank.yaml").exists():
            return p

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="FSM template directory not found",
    )


def _list_fsm_templates() -> list[str]:
    """Return sorted list of FSM template filenames (.yaml/.yml)."""
    fsm_dir = _find_fsm_template_dir()
    names = []
    for f in fsm_dir.iterdir():
        if f.is_file() and f.suffix.lower() in (".yaml", ".yml"):
            names.append(f.name)
    return sorted(names)


def _get_fsm_template_path(filename: str) -> Path:
    """Get path to an FSM template file; filename must be in allowlist."""
    safe_name = Path(filename).name
    if safe_name != filename or ".." in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )
    allowed = _list_fsm_templates()
    if safe_name not in allowed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FSM template not found: {filename}. Available: {allowed[:10]}{'...' if len(allowed) > 10 else ''}",
        )
    return _find_fsm_template_dir() / safe_name


@router.get(
    "/templates/fsm",
    summary="List FSM template filenames",
    description="Return a list of available FSM template filenames (e.g. blank.yaml, order_management.yaml). Use GET /templates/fsm/{filename} to get one.",
    response_description="JSON object with templates array",
    tags=["Templates"],
)
async def list_fsm_templates():
    """List available FSM template filenames."""
    try:
        names = _list_fsm_templates()
        return {"templates": names}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing FSM templates: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list FSM templates: {str(e)}",
        )


@router.get(
    "/templates/fsm/{filename:path}",
    summary="Get FSM template content",
    description="Return a single FSM template as YAML text by filename (e.g. blank.yaml, order_management.yaml).",
    response_class=PlainTextResponse,
    tags=["Templates"],
)
async def get_fsm_template(filename: str):
    """Return one FSM template file content as YAML text."""
    try:
        template_path = _get_fsm_template_path(filename)
        content = template_path.read_text(encoding="utf-8")
        return PlainTextResponse(content=content, media_type="application/x-yaml")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error serving FSM template %s: %s", filename, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve FSM template: {str(e)}",
        )
