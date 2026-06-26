from fastapi import FastAPI

from app.businesses.presentation.router import router as business_router
from app.holidays.presentation.router import router as holidays_router
from app.core.exception_handler import register_exception_handlers

app = FastAPI(title="Easy Payroll API")

register_exception_handlers(app)

app.include_router(business_router, prefix="/businesses", tags=["Businesses"])
app.include_router(holidays_router, prefix="/businesses/{business_id}/holidays", tags=["Holidays"])

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
