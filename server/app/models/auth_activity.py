from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.models.base import BaseModel
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import Boolean

class AuthActivity(BaseModel):
    __tablename__ = "auth_activity"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_auth_id = Column(Integer, ForeignKey("user_auth.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address = Column(String(100), nullable=False)
    user_agent = Column(String(500), nullable=False)
    is_successful = Column(Boolean, default=True, nullable=False)
    login_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    logout_time = Column(DateTime, nullable=True)
    

    user = relationship("User", back_populates="auth_activity")
    user_auth = relationship("UserAuth", back_populates="auth_activity")