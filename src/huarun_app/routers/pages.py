import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from huarun_app.database import get_db
from huarun_app.models import Medicine, MedicineScan, User


router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")


def _page_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


def _redirect_login() -> RedirectResponse:
    return RedirectResponse("/login", status_code=303)


def _context(request: Request, page_id: str, **extra: Any) -> dict[str, Any]:
    return {"request": request, "page_id": page_id, **extra}


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        _context(request, "login", hide_nav=True),
    )


@router.get("/")
def home_page(request: Request, db: Session = Depends(get_db)):
    user = _page_user(request, db)
    if user is None:
        return _redirect_login()
    return templates.TemplateResponse(request, "index.html", _context(request, "home", user=user))


@router.get("/upload")
def upload_page(request: Request, db: Session = Depends(get_db)):
    if _page_user(request, db) is None:
        return _redirect_login()
    return templates.TemplateResponse(request, "upload.html", _context(request, "upload"))


@router.get("/confirm/{scan_id}")
def confirm_page(scan_id: int, request: Request, db: Session = Depends(get_db)):
    user = _page_user(request, db)
    if user is None:
        return _redirect_login()
    scan = db.get(MedicineScan, scan_id)
    if scan is None or scan.user_id != user.id:
        return RedirectResponse("/upload", status_code=303)
    extraction = json.loads(scan.extraction_json)
    return templates.TemplateResponse(
        request,
        "confirm.html",
        _context(
            request,
            "confirm",
            scan_id=scan.id,
            image_url=f"/uploads/{scan.image_path}",
            extraction=extraction,
            warning_text="。".join(extraction.get("warnings", [])),
        ),
    )


@router.get("/pillbox")
def pillbox_page(request: Request, db: Session = Depends(get_db)):
    if _page_user(request, db) is None:
        return _redirect_login()
    return templates.TemplateResponse(request, "pillbox.html", _context(request, "pillbox"))


@router.get("/reminders")
def reminders_page(request: Request, db: Session = Depends(get_db)):
    if _page_user(request, db) is None:
        return _redirect_login()
    return templates.TemplateResponse(request, "reminders.html", _context(request, "reminders"))


@router.get("/qa")
def qa_page(request: Request, db: Session = Depends(get_db)):
    user = _page_user(request, db)
    if user is None:
        return _redirect_login()
    medicines = db.scalars(
        select(Medicine).where(Medicine.user_id == user.id).order_by(Medicine.id)
    ).all()
    return templates.TemplateResponse(
        request,
        "qa.html",
        _context(request, "qa", medicines=medicines),
    )
