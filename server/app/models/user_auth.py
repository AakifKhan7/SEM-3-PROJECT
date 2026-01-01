from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel

class UserAuth(BaseModel):
    __tablename__ = "user_auth"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    
    user = relationship("User", back_populates="auth")
    auth_activity = relationship("AuthActivity", back_populates="user_auth")

