from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, func

from app.database import Base


class User(Base):
    """User account model for authentication and role-based authorization."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # "admin" or "user"
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Employee(Base):
    """Employee record model for company personnel management."""

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    department = Column(String(80), nullable=False, index=True)
    position = Column(String(80), nullable=False)
    salary = Column(Float, nullable=False)
    phone = Column(String(30), nullable=True)
    # Status can be: "active", "on_leave", "terminated"
    status = Column(String(20), nullable=False, default="active")
    hired_on = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
