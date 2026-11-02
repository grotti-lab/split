"""The web app: server-rendered pages that work on phones and computers.

This is the scaffold Grotti's team starts from: it runs, it has a database,
and the golden sets are wired as tests. The features are the team's work
(BRIEF.md, .mycelium/specs).

    uv run uvicorn --factory split.app:create_app --reload
"""

from __future__ import annotations

import os
from pathlib import Path

import re
import secrets

from fastapi import Form, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import db

TEMPLATES = Jinja2Templates(directory=Path(__file__).parent / "templates")


def create_app(db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Split")
    app.state.db_path = Path(db_path or os.environ.get("SPLIT_DB", "split.db"))
    db.init(app.state.db_path)

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> HTMLResponse:
        return TEMPLATES.TemplateResponse(request, "home.html", {})

    @app.post("/groups")
    def create_group(name: str = Form(...), members: str = Form(...)) -> RedirectResponse:
        # members: names separated by commas or new lines
        names: list[str] = []
        for n in re.split(r"[,\n]", members):
            n = n.strip()
            if n and n not in names:
                names.append(n)
        if not name.strip() or not names:
            raise HTTPException(422, "A group needs a name and at least one member")
        slug = secrets.token_urlsafe(8)
        db.create_group(app.state.db_path, slug, name.strip(), names)
        return RedirectResponse(f"/groups/{slug}", status_code=303)

    @app.get("/groups/{slug}", response_class=HTMLResponse)
    def show_group(request: Request, slug: str) -> HTMLResponse:
        group = db.get_group(app.state.db_path, slug)
        if group is None:
            raise HTTPException(404, "No such group")
        return TEMPLATES.TemplateResponse(request, "group.html", {"group": group})

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app
