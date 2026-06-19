from app.db.session import SessionLocal
from app.db.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str):
    return pwd_context.hash(password)

def create_admin_user():
    db = SessionLocal()

    try:
        admin_email = "admin@example.com"
        print(f"Creating admin user with email: {admin_email} and password: admin123")
        admin = User(
            email=admin_email,
            password_hash=hash_password("admin123"),
            role="admin"
        )

        db.add(admin)
        db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
    print("Admin user created")