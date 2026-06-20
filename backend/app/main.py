from fastapi import FastAPI
from app.business.presentation.router import router as business_router
from app.core.exception_handler import register_business_exception_handlers

app = FastAPI(title="Easy Payroll API")

# Later we'll do: from app.business.presentation.router import router as business_router
# and then app.include_router(business_router, prefix="/businesses", tags=["businesses"])
app.include_router(business_router)

register_business_exception_handlers(app)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
