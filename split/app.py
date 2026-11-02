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
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from . import balances, db, money

TEMPLATES = Jinja2Templates(directory=Path(__file__).parent / "templates")


def same_name(a: str, b: str) -> bool:
    """Are two member names the same? Capitals don't matter: "ana" is "Ana"."""
    return a.casefold() == b.casefold()


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

    def _group_context(group: dict, slug: str) -> dict:
        expenses = db.list_expenses(app.state.db_path, slug)
        for e in expenses:
            e["amount_text"] = money.format_amount(e["amount"])
            e["shares_text"] = [(n, money.format_amount(c)) for n, c in e["shares"]]
        nets = balances.balances(group["members"], expenses)
        return {
            "group": group, "expenses": expenses,
            "balances": [(n, balances.net_text(nets[n])) for n in group["members"]],
            "payments": [balances.payment_text(p) for p in balances.suggested_payments(nets)],
        }

    @app.get("/groups/{slug}", response_class=HTMLResponse)
    def show_group(request: Request, slug: str) -> HTMLResponse:
        group = db.get_group(app.state.db_path, slug)
        if group is None:
            raise HTTPException(404, "No such group")
        return TEMPLATES.TemplateResponse(request, "group.html", _group_context(group, slug))

    @app.post("/groups/{slug}/members")
    def add_member(request: Request, slug: str, name: str = Form(...)) -> RedirectResponse:
        name = name.strip()
        if not name:
            raise HTTPException(422, "A member needs a name")
        group = db.get_group(app.state.db_path, slug)
        if group is None:
            raise HTTPException(404, "No such group")
        existing = next((m for m in group["members"] if same_name(name, m)), None)
        if existing is not None:
            return TEMPLATES.TemplateResponse(
                request, "group.html",
                {**_group_context(group, slug), "message": f"There is already an {existing} in this group"},
                status_code=409,
            )
        db.add_member(app.state.db_path, slug, name)
        return RedirectResponse(f"/groups/{slug}", status_code=303)

    @app.post("/groups/{slug}/members/remove")
    def remove_member(request: Request, slug: str, name: str = Form(...)) -> Response:
        group = db.get_group(app.state.db_path, slug)
        if group is None:
            raise HTTPException(404, "No such group")
        result = db.remove_member(app.state.db_path, slug, name)
        if result == "missing":
            raise HTTPException(404, "No such member")
        if result == "has_expenses":
            return TEMPLATES.TemplateResponse(
                request, "group.html",
                {**_group_context(group, slug), "message": f"{name} has expenses in this group, so they can't be removed"},
                status_code=409,
            )
        return RedirectResponse(f"/groups/{slug}", status_code=303)

    @app.post("/groups/{slug}/expenses")
    def add_expense(
        request: Request, slug: str, description: str = Form(...), amount: str = Form(...), payer: str = Form(...),
        sharing: list[str] = Form(default=[]),
    ) -> Response:
        group = db.get_group(app.state.db_path, slug)
        if group is None:
            raise HTTPException(404, "No such group")
        if not description.strip() or payer not in group["members"]:
            raise HTTPException(422, "An expense needs a description and a payer from the group")
        try:
            cents = money.parse_amount(amount)
        except ValueError:
            cents = 0  # not a number, or negative: refused like zero
        if cents <= 0:
            return TEMPLATES.TemplateResponse(
                request, "group.html",
                {**_group_context(group, slug), "message": "Enter an amount above zero"},
                status_code=422,
            )
        # equal split between the members sharing (everyone if none are chosen), in the group's order
        if any(n not in group["members"] for n in sharing):
            raise HTTPException(422, "Only members of the group can share an expense")
        sharers = [m for m in group["members"] if m in sharing] or group["members"]
        shares = money.split_equally(cents, sharers, payer)
        db.add_expense(app.state.db_path, slug, description.strip(), cents, payer, shares)
        return RedirectResponse(f"/groups/{slug}", status_code=303)

    @app.post("/groups/{slug}/expenses/{expense_id}/delete")
    def delete_expense(slug: str, expense_id: int) -> RedirectResponse:
        # allowed even after settling up (Amina's decision #3)
        if not db.delete_expense(app.state.db_path, slug, expense_id):
            raise HTTPException(404, "No such expense")
        return RedirectResponse(f"/groups/{slug}", status_code=303)

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app
