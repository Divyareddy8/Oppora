from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import Profile, User
from ..schemas import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    email = str(data.email).lower()
    if not email.endswith("@gmail.com"):
        raise HTTPException(status_code=400, detail="Please register with a Gmail address")
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=email, password_hash=hash_password(data.password))
    db.add(user)
    db.flush()

    db.add(Profile(user_id=user.id))
    db.commit()
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"access_token": create_access_token(user.id), "token_type": "bearer"}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email}
