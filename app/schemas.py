from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------
# User & Authentication Schemas
# ---------------------------------------------------------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str | None = Field(default=None, max_length=100)


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    full_name: str | None = None
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "user"
    username: str = ""


# ---------------------------------------------------------
# Employee Schemas
# ---------------------------------------------------------
class EmployeeBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    department: str = Field(..., min_length=2, max_length=80)
    position: str = Field(..., min_length=2, max_length=80)
    salary: float = Field(..., gt=0, description="Annual or monthly salary amount")
    phone: str | None = Field(default=None, max_length=30)
    status: str = Field(default="active", pattern="^(active|on_leave|terminated)$")


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    department: str | None = Field(default=None, min_length=2, max_length=80)
    position: str | None = Field(default=None, min_length=2, max_length=80)
    salary: float | None = Field(default=None, gt=0)
    phone: str | None = Field(default=None, max_length=30)
    status: str | None = Field(default=None, pattern="^(active|on_leave|terminated)$")


class EmployeeOut(EmployeeBase):
    id: int
    hired_on: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeStats(BaseModel):
    total_employees: int
    total_departments: int
    total_payroll: float
    average_salary: float
    department_counts: dict[str, int]
    status_counts: dict[str, int]


# ---------------------------------------------------------
# Health Check Schemas
# ---------------------------------------------------------
class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class ReadinessCheck(BaseModel):
    status: str
    database: str
    timestamp: datetime
