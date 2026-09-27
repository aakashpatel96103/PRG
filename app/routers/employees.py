from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_current_user, get_db, require_admin

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get(
    "/stats/summary",
    response_model=schemas.EmployeeStats,
    summary="Get aggregated employee statistics",
)
def get_employee_stats(
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    """Calculates summary metrics across all employee records."""
    total_employees = db.query(models.Employee).count()
    if total_employees == 0:
        return schemas.EmployeeStats(
            total_employees=0,
            total_departments=0,
            total_payroll=0.0,
            average_salary=0.0,
            department_counts={},
            status_counts={},
        )

    payroll_data = db.query(
        func.sum(models.Employee.salary).label("total"),
        func.avg(models.Employee.salary).label("average"),
    ).first()

    total_payroll = float(payroll_data.total or 0.0)
    avg_salary = float(payroll_data.average or 0.0)

    dept_rows = (
        db.query(models.Employee.department, func.count(models.Employee.id))
        .group_by(models.Employee.department)
        .all()
    )
    department_counts = {dept: count for dept, count in dept_rows}

    status_rows = (
        db.query(models.Employee.status, func.count(models.Employee.id))
        .group_by(models.Employee.status)
        .all()
    )
    status_counts = {st: count for st, count in status_rows}

    return schemas.EmployeeStats(
        total_employees=total_employees,
        total_departments=len(department_counts),
        total_payroll=round(total_payroll, 2),
        average_salary=round(avg_salary, 2),
        department_counts=department_counts,
        status_counts=status_counts,
    )


@router.get(
    "/",
    response_model=list[schemas.EmployeeOut],
    summary="List and search employees",
)
def list_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    department: str | None = None,
    employee_status: str | None = Query(None, alias="status"),
    q: str | None = Query(None, description="Search term for name or email"),
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    """Retrieves paginated employee records with optional department,
    status, and text search filters.
    """
    query = db.query(models.Employee)

    if department:
        query = query.filter(models.Employee.department.ilike(f"%{department}%"))
    if employee_status:
        query = query.filter(models.Employee.status == employee_status)
    if q:
        search_pattern = f"%{q}%"
        query = query.filter(
            models.Employee.full_name.ilike(search_pattern)
            | models.Employee.email.ilike(search_pattern)
            | models.Employee.position.ilike(search_pattern)
        )

    return query.order_by(models.Employee.id.desc()).offset(skip).limit(limit).all()


@router.get(
    "/{employee_id}",
    response_model=schemas.EmployeeOut,
    summary="Get single employee by ID",
)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    """Fetches details for a specific employee."""
    employee = db.get(models.Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found",
        )
    return employee


@router.post(
    "/",
    response_model=schemas.EmployeeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee (Admin only)",
)
def create_employee(
    employee_in: schemas.EmployeeCreate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    """Creates a new employee record. Requires Admin role."""
    employee = models.Employee(**employee_in.model_dump())
    db.add(employee)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee with email '{employee_in.email}' already exists",
        ) from None
    db.refresh(employee)
    return employee


@router.put(
    "/{employee_id}",
    response_model=schemas.EmployeeOut,
    summary="Update employee (Admin only)",
)
def update_employee(
    employee_id: int,
    employee_in: schemas.EmployeeUpdate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    """Updates an existing employee record. Requires Admin role."""
    employee = db.get(models.Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found",
        )

    update_data = employee_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee with this email already exists",
        ) from None
    db.refresh(employee)
    return employee


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete employee (Admin only)",
)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    """Deletes an employee record from the system. Requires Admin role."""
    employee = db.get(models.Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found",
        )
    db.delete(employee)
    db.commit()
    return None
