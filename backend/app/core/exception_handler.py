from app.business.presentation.exception_handler import (
    register_business_exception_handlers,
)


def register_exception_handlers(app):
    register_business_exception_handlers(app)
