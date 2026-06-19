from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import Request, Form
from fastapi.templating import Jinja2Templates
from app.db.session import get_db
from app.db.models import User
from app.auth.security import (verify_password, create_access_token)
from app.auth.dependencies import (get_current_user)
from fastapi.responses import RedirectResponse

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        { "request": request }
    )

@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    access_token = create_access_token(
        {
            "user_id": user.id,
            "role": user.role
        }
    )
    print(f"Generated token for user {user.email} with role {user.role}")
    response = RedirectResponse(
        url="/dashboard",
        status_code=303
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True
    )

    return response

@router.get("/me")
def me(
    current_user: User = Depends(
        get_current_user
    )
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }


@router.post("/logout")
def logout():
    return {
        "message": "Logout successful"
    }