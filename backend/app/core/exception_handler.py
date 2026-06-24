from app.businesses.presentation.exception_handler import (
    register_business_exception_handlers,
)

def register_exception_handlers(app) -> None:
    register_business_exception_handlers(app)

