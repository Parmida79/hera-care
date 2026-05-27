from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.utils import authorize, get_current_user, authenticate_user_db, \
    create_access_token, hash_password
from app.db.database import get_db
from app.models import Member, Patient
from app.schemas import MemberResponse, LoginBase, SignUpBase, TokenResponse

limited_auth_router = APIRouter()
public_auth_router = APIRouter()
restricted_auth_router = APIRouter()

@public_auth_router.post('/signup', response_model=MemberResponse)
def sign_up(
        request: Request,
        payload: SignUpBase,
        session: Session = Depends(get_db)
):
    username = payload.username.strip().lower()
    existing = session.execute(
        select(Member).where(Member.username == username)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    patient = Patient(
        username=username,
        hashed_password=hash_password(payload.password),
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role="patient"
    )
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return patient


@public_auth_router.post('/login', response_model=TokenResponse)
def login(payload: LoginBase, db: Session = Depends(get_db)):
    user = authenticate_user_db(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    token = create_access_token(subject=user.username, role=user.role)
    return {"access_token": token, "token_type": "bearer"}


@restricted_auth_router.get("/me", response_model=MemberResponse)
def get_current_profile(current_user: Member = Depends(get_current_user)):
    return current_user
