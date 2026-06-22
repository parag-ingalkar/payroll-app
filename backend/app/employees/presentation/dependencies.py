from fastapi import Depends

from app.core.dependencies import get_uow
from app.core.uow import SqlAlchemyUnitOfWork
from app.employees.application.use_cases import (
    CreateEmployeeUseCase,
    DeleteEmployeeUseCase,
    GetEmployeeByIdUseCase,
    ListEmployeesUseCase,
    UpdateEmployeeUseCase,
)


def get_create_employee_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> CreateEmployeeUseCase:
    return CreateEmployeeUseCase(uow)


def get_list_employees_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ListEmployeesUseCase:
    return ListEmployeesUseCase(uow)


def get_get_employee_by_id_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GetEmployeeByIdUseCase:
    return GetEmployeeByIdUseCase(uow)


def get_update_employee_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> UpdateEmployeeUseCase:
    return UpdateEmployeeUseCase(uow)


def get_delete_employee_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> DeleteEmployeeUseCase:
    return DeleteEmployeeUseCase(uow)
