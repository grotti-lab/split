"""The web app: server-rendered pages that work on phones and computers.

This is the scaffold Grotti's team starts from: it runs, it has a database,
and the golden sets are wired as tests. The features are the team's work
(BRIEF.md, .mycelium/specs).

    uv run uvicorn --factory split.app:create_app --reload
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app
