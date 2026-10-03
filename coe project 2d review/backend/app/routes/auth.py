from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.schema import User
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Authentication & Users"])

class UserSchema(BaseModel):
    id: str
    username: str
    name: str
    role: str
    department: str

    class Config:
        from_attributes = True

@router.get("/users", response_model=List[UserSchema])
def list_users(db: Session = Depends(get_db)):
    """Returns all synthetic hospital users for role switching."""
    return db.query(User).all()

@router.get("/user/{user_id}", response_model=UserSchema)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
