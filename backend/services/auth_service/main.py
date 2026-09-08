from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
import logging
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import bcrypt
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth-service")

app = FastAPI(title="SSSCANER Auth Service", version="1.0.0")

JWT_SECRET = os.getenv("JWT_SECRET", "ssscaner-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

security = HTTPBearer()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash.encode())

def create_token(user_id: str, email: str) -> tuple[str, int]:
    expires = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expires,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, int(expires.timestamp())

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth-service"}

@app.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = f"user_{datetime.utcnow().timestamp()}".replace(".", "_")
    user = User(
        id=user_id,
        email=request.email,
        password_hash=hash_password(request.password),
        name=request.name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token, expires = create_token(user.id, user.email)
    redis_client.set(f"token:{token}", user.id, ex=JWT_EXPIRATION_HOURS * 3600)
    logger.info(f"User registered: {user.email}")
    return TokenResponse(access_token=token, token_type="bearer", expires_in=JWT_EXPIRATION_HOURS * 3600)

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token, expires = create_token(user.id, user.email)
    redis_client.set(f"token:{token}", user.id, ex=JWT_EXPIRATION_HOURS * 3600)
    logger.info(f"User logged in: {user.email}")
    return TokenResponse(access_token=token, token_type="bearer", expires_in=JWT_EXPIRATION_HOURS * 3600)

@app.post("/api/v1/auth/verify")
async def verify(credentials: HTTPAuthCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    cached_user_id = redis_client.get(f"token:{token}")
    if cached_user_id:
        user = db.query(User).filter(User.id == cached_user_id).first()
        if user:
            return {"user_id": user.id, "email": user.email, "name": user.name}
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        email = payload.get("email")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        redis_client.set(f"token:{token}", user.id, ex=3600)
        return {"user_id": user.id, "email": user.email, "name": user.name}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
