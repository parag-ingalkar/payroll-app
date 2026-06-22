from fastapi import FastAPI

from app.attendance.presentation.router import router as attendance_router
from app.business.presentation.router import router as business_router
from app.core.exception_handler import register_exception_handlers
from app.employees.presentation.router import router as employees_router
from app.holidays.presentation.router import router as holidays_router

app = FastAPI(title="Easy Payroll API")

register_exception_handlers(app)

app.include_router(business_router, prefix="/businesses", tags=["Businesses"])
app.include_router(
    holidays_router, prefix="/businesses/{business_id}/holidays", tags=["Holidays"]
)
app.include_router(
    employees_router, prefix="/businesses/{business_id}/employees", tags=["Employees"]
)
app.include_router(
    attendance_router,
    prefix="/businesses/{business_id}/attendance",
    tags=["Attendance"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
