"""Template/rules management endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/rules", tags=["rules"])


class TemplateInfo(BaseModel):
    """Information about a template."""
    name: str
    source: str  # built-in, global, local
    path: Optional[str] = None
    description: Optional[str] = None


class TemplateContent(BaseModel):
    """Template content."""
    name: str
    content: str
    source: str


@router.get("/list")
async def list_templates():
    """List all templates and their active sources."""
    templates = [
        TemplateInfo(
            name="spec",
            source="built-in",
            description="Feature specification template",
        ),
        TemplateInfo(
            name="tasks",
            source="built-in",
            description="Implementation tasks template",
        ),
        TemplateInfo(
            name="project",
            source="built-in",
            description="PROJECT.md template",
        ),
        TemplateInfo(
            name="focus",
            source="built-in",
            description="Team focus template",
        ),
        TemplateInfo(
            name="pr-review",
            source="built-in",
            description="PR review template",
        ),
    ]

    # TODO: Check for custom templates in .emdash-rules

    return {"templates": templates}


@router.get("/{template_name}", response_model=TemplateContent)
async def get_template(template_name: str):
    """Get a template's content."""
    try:
        from ..templates import load_template as get_template

        content = get_template(template_name)
        if not content:
            raise HTTPException(status_code=404, detail=f"Template {template_name} not found")

        return TemplateContent(
            name=template_name,
            content=content,
            source="built-in",  # TODO: Detect actual source
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/init")
async def init_templates(global_templates: bool = False, force: bool = False):
    """Initialize custom templates in .emdash-rules."""
    try:
        from pathlib import Path

        # Determine target directory
        if global_templates:
            target = Path.home() / ".emdash-rules"
        else:
            target = Path.cwd() / ".emdash-rules"

        if target.exists() and not force:
            raise HTTPException(
                status_code=400,
                detail=f"Templates already exist at {target}. Use force=true to overwrite."
            )

        target.mkdir(parents=True, exist_ok=True)

        # Copy built-in templates
        from ..templates.loader import get_defaults_dir, copy_templates_to_dir, TEMPLATE_NAMES

        templates_copied = copy_templates_to_dir(target, overwrite=force)

        return {
            "success": True,
            "path": str(target),
            "templates": templates_copied,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
