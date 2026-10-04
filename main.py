import os
import json
import calendar
from datetime import datetime, date
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Depends, HTTPException, Request, Response, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from database import engine, Base, get_db
import models
from auth import hash_password, verify_password
from ai_service import generate_health_summary

# Resolve base directory for serverless environments (e.g. Vercel)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Auto-create tables on launch (with error suppression for serverless cold-starts)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Table creation skipped/failed on startup: {e}")

app = FastAPI(title="HealthTuner", description="Intelligent Health Companion Web Application")

# Mount Static Files & Jinja2 Templates with absolute path resolution
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir)


# --- Authentication Dependency ---
def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    try:
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        return user
    except Exception:
        return None

def require_auth(request: Request, db: Session = Depends(get_db)) -> models.User:
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    return user


# --- Pydantic Schemas ---
class DailyLogCreate(BaseModel):
    date: str
    workload_type: str
    content_json: Dict[str, Any]

class SummaryGenerateRequest(BaseModel):
    start_date: str
    end_date: str


# --- Web Page Routes ---

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"user": None, "error": None}
    )


@app.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email.strip().lower()).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"user": None, "error": "Invalid email or password."},
            status_code=400
        )
    
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True, max_age=86400 * 30, samesite="lax")
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"user": None, "error": None}
    )


@app.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    clean_email = email.strip().lower()
    existing = db.query(models.User).filter(models.User.email == clean_email).first()
    if existing:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"user": None, "error": "An account with this email already exists."},
            status_code=400
        )
    
    new_user = models.User(
        name=name.strip(),
        email=clean_email,
        password_hash=hash_password(password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Auto-login upon registration and redirect straight to dashboard
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="user_id", value=str(new_user.id), httponly=True, max_age=86400 * 30, samesite="lax")
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("user_id")
    return response


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    today = date.today()
    year = today.year
    month = today.month
    month_name = calendar.month_name[month]

    # Calculate month calendar grid
    cal = calendar.Calendar(firstweekday=0) # 0 is Monday
    month_days = cal.monthdays2calendar(year, month) # Returns weeks with (day_num, weekday)

    # Fetch all user logs for current month
    start_of_month = date(year, month, 1)
    if month == 12:
        end_of_month = date(year + 1, 1, 1)
    else:
        end_of_month = date(year, month + 1, 1)

    logs = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == user.id,
        models.DailyLog.date >= start_of_month,
        models.DailyLog.date < end_of_month
    ).all()

    logs_by_date = {log.date.strftime("%Y-%m-%d"): {
        "id": log.id,
        "date": log.date.strftime("%Y-%m-%d"),
        "workload_type": log.workload_type,
        "content_json": log.content_json
    } for log in logs}

    calendar_cells = []
    for week in month_days:
        for day_num, weekday in week:
            if day_num == 0:
                calendar_cells.append({
                    "is_padding": True,
                    "day_num": 0
                })
            else:
                cell_date = date(year, month, day_num)
                date_str = cell_date.strftime("%Y-%m-%d")
                is_future = cell_date > today
                is_today = cell_date == today
                has_log = date_str in logs_by_date

                calendar_cells.append({
                    "is_padding": False,
                    "day_num": day_num,
                    "date_str": date_str,
                    "is_future": is_future,
                    "is_today": is_today,
                    "has_log": has_log,
                    "log": logs_by_date.get(date_str)
                })

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "month_name": month_name,
            "current_year": year,
            "calendar_cells": calendar_cells,
            "logs_by_date_json": json.dumps(logs_by_date)
        }
    )


@app.get("/timeline", response_class=HTMLResponse)
async def timeline_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    today = date.today()
    default_start = date(today.year, today.month, 1).strftime("%Y-%m-%d")
    default_end = today.strftime("%Y-%m-%d")

    summaries = db.query(models.AISummary).filter(
        models.AISummary.user_id == user.id
    ).order_by(models.AISummary.created_at.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="timeline.html",
        context={
            "user": user,
            "summaries": summaries,
            "default_start": default_start,
            "default_end": default_end
        }
    )


# --- JSON API Endpoints for Logs and AI Summaries ---

@app.post("/api/logs")
async def save_daily_log(
    payload: DailyLogCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        log_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    if log_date > date.today():
        raise HTTPException(status_code=400, detail="Cannot log entries for future dates.")

    if payload.workload_type not in ["easy", "medium", "maximum"]:
        raise HTTPException(status_code=400, detail="Invalid workload type.")

    # Upsert log entry
    existing_log = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == user.id,
        models.DailyLog.date == log_date
    ).first()

    if existing_log:
        existing_log.workload_type = payload.workload_type
        existing_log.content_json = payload.content_json
        db.commit()
        db.refresh(existing_log)
        return {"status": "success", "message": "Log updated successfully", "log_id": existing_log.id}
    else:
        new_log = models.DailyLog(
            user_id=user.id,
            date=log_date,
            workload_type=payload.workload_type,
            content_json=payload.content_json
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return {"status": "success", "message": "Log created successfully", "log_id": new_log.id}


@app.delete("/api/logs/{date_str}")
async def delete_daily_log(
    date_str: str,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format.")

    log_entry = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == user.id,
        models.DailyLog.date == log_date
    ).first()

    if not log_entry:
        raise HTTPException(status_code=404, detail="Log not found.")

    db.delete(log_entry)
    db.commit()
    return {"status": "success", "message": "Log deleted successfully."}


@app.post("/api/summaries/generate")
async def create_ai_summary(
    payload: SummaryGenerateRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        start_d = datetime.strptime(payload.start_date, "%Y-%m-%d").date()
        end_d = datetime.strptime(payload.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format.")

    if start_d > end_d:
        raise HTTPException(status_code=400, detail="Start date cannot be after end date.")

    # Retrieve logs within date window
    logs = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == user.id,
        models.DailyLog.date >= start_d,
        models.DailyLog.date <= end_d
    ).order_by(models.DailyLog.date.asc()).all()

    serialized_logs = [
        {
            "date": l.date.strftime("%Y-%m-%d"),
            "workload_type": l.workload_type,
            "content_json": l.content_json
        }
        for l in logs
    ]

    summary_text = await generate_health_summary(
        logs=serialized_logs,
        start_date=payload.start_date,
        end_date=payload.end_date
    )

    ai_record = models.AISummary(
        user_id=user.id,
        start_date=start_d,
        end_date=end_d,
        summary_text=summary_text
    )
    db.add(ai_record)
    db.commit()
    db.refresh(ai_record)

    return {
        "status": "success",
        "summary_id": ai_record.id,
        "summary_text": summary_text
    }


@app.delete("/api/summaries/{summary_id}")
async def delete_ai_summary(
    summary_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")

    summary = db.query(models.AISummary).filter(
        models.AISummary.id == summary_id,
        models.AISummary.user_id == user.id
    ).first()

    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found.")

    db.delete(summary)
    db.commit()
    return {"status": "success", "message": "Summary deleted successfully."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
