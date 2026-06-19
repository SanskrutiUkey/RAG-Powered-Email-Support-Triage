from fastapi import Depends, HTTPException
from fastapi import Request
from app.db.session import SessionLocal
from app.db.models import User
from app.auth.security import decode_access_token


def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    # Support tokens prefixed with "Bearer " if present
    if isinstance(token, str) and token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]

    db = SessionLocal()
    try:
        payload = decode_access_token(token)

        user_id = payload.get("user_id") or payload.get("sub")

        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")

        return user

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    finally:
        db.close()


def require_admin(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    print("current_user:", current_user.email, current_user.role)
    return current_user


def require_agent(
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "agent"]:
        raise HTTPException(
            status_code=403,
            detail="Agent access required"
        )

    return current_user