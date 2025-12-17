from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.sql import func
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(512), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text)
    price = Column(Float, default=0.0)
    category = Column(String(255), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String(32), nullable=False)  # user/system/assistant
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(128), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip = Column(String(64))
    action = Column(String(255))
    payload = Column(Text)
    result = Column(Text)
    pii_flag = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReindexCheckpoint(Base):
    __tablename__ = "reindex_checkpoints"
    id = Column(Integer, primary_key=True, index=True)
    collection = Column(String(255), nullable=False, index=True)
    last_processed_id = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
