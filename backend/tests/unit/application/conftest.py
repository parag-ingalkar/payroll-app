# tests/unit/application/conftest.py
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.attendance.application.ports import AttendanceRepositoryPort
from app.attendance.domain.entities import Attendance, AttendanceStatus
from app.business.application.ports import BusinessRepositoryPort
from app.business.domain.entities import Business, WageType
from app.business.domain.value_objects import normalize_business_name_for_lookup
from app.core.uow import UnitOfWorkPort
from app.employees.application.ports import EmployeeRepositoryPort
from app.employees.domain.entities import Employee
from app.holidays.application.ports import HolidayRepositoryPort
from app.holidays.domain.entities import Holiday


class InMemoryBusinessRepository(BusinessRepositoryPort):
    def __init__(self, items: list[Business] | None = None) -> None:
        self._items: list[Business] = list(items or [])

    async def add(self, business: Business) -> None:
        if business.id is None:
            business.id = uuid4()
        self._items.append(business)

    async def get_by_id_and_owner(
        self, business_id: UUID, owner_id: str
    ) -> Business | None:
        return next(
            (b for b in self._items if b.id == business_id and b.owner_id == owner_id),
            None,
        )

    async def list_by_owner(self, owner_id: str) -> Sequence[Business]:
        return [b for b in self._items if b.owner_id == owner_id]

    async def find_by_normalized_name(
        self, owner_id: str, normalized_name: str
    ) -> Business | None:
        for b in self._items:
            if b.owner_id != owner_id:
                continue
            if normalize_business_name_for_lookup(b.name) == normalized_name:
                return b
        return None

    async def find_by_owner_and_name(self, owner_id: str, name: str) -> Business | None:
        normalized_name = normalize_business_name_for_lookup(name)
        for b in self._items:
            if b.owner_id != owner_id:
                continue
            if normalize_business_name_for_lookup(b.name) == normalized_name:
                return b
        return None

    async def delete(self, business: Business) -> None:
        self._items = [b for b in self._items if b is not business]

    async def update(self, business: Business) -> None:
        for idx, b in enumerate(self._items):
            if b.id == business.id:
                self._items[idx] = business
                return


class InMemoryHolidayRepository(HolidayRepositoryPort):
    def __init__(self, items: list[Holiday] | None = None) -> None:
        self._items: list[Holiday] = list(items or [])

    async def add(self, holiday: Holiday) -> None:
        if holiday.id is None:
            holiday.id = uuid4()
        self._items.append(holiday)

    async def get_by_business_and_date(
        self, business_id: UUID, date_: date
    ) -> Holiday | None:
        return next(
            (
                h
                for h in self._items
                if h.business_id == business_id and h.date == date_
            ),
            None,
        )

    async def get_by_business_and_id(
        self, business_id: UUID, holiday_id: UUID
    ) -> Holiday | None:
        return next(
            (
                h
                for h in self._items
                if h.business_id == business_id and h.id == holiday_id
            ),
            None,
        )

    async def list_by_business(
        self, business_id: UUID, year: int | None = None, month: int | None = None
    ) -> Sequence[Holiday]:
        result = [h for h in self._items if h.business_id == business_id]
        if year is not None:
            result = [h for h in result if h.date.year == year]
        if month is not None:
            result = [h for h in result if h.date.month == month]
        return result

    async def delete_by_business_and_date(self, business_id: UUID, date_: date) -> None:
        self._items = [
            h
            for h in self._items
            if not (h.business_id == business_id and h.date == date_)
        ]

    async def update(self, holiday: Holiday) -> None:
        for idx, h in enumerate(self._items):
            if h.id == holiday.id and h.business_id == holiday.business_id:
                self._items[idx] = holiday
                return


class InMemoryEmployeeRepository(EmployeeRepositoryPort):
    def __init__(self, items: list[Employee] | None = None) -> None:
        self._items: list[Employee] = list(items or [])

    async def add(self, employee: Employee) -> None:
        self._items.append(employee)

    async def get_by_business_and_id(
        self, business_id: UUID, employee_id: UUID
    ) -> Employee | None:
        return next(
            (
                e
                for e in self._items
                if e.business_id == business_id and e.id == employee_id
            ),
            None,
        )

    async def list_by_business(
        self, business_id: UUID, is_active: bool | None = None
    ) -> Sequence[Employee]:
        result = [e for e in self._items if e.business_id == business_id]
        if is_active is not None:
            result = [e for e in result if e.is_active == is_active]
        return result

    async def update(self, employee: Employee) -> None:
        for idx, e in enumerate(self._items):
            if e.id == employee.id and e.business_id == employee.business_id:
                self._items[idx] = employee
                return

    async def delete(self, employee: Employee) -> None:
        self._items = [
            e
            for e in self._items
            if not (e.business_id == employee.business_id and e.id == employee.id)
        ]


class InMemoryAttendanceRepository(AttendanceRepositoryPort):
    def __init__(self, items: list[Attendance] | None = None) -> None:
        self._items: list[Attendance] = list(items or [])

    async def add(self, attendance: Attendance) -> None:
        self._items.append(attendance)

    async def get_by_employee_and_date(
        self, business_id: UUID, employee_id: UUID, date_: date
    ) -> Attendance | None:
        return next(
            (
                a
                for a in self._items
                if a.business_id == business_id
                and a.employee_id == employee_id
                and a.date == date_
            ),
            None,
        )

    async def list_by_date(
        self,
        business_id: UUID,
        date_: date,
        employee_id: UUID | None = None,
        status: AttendanceStatus | None = None,
    ) -> Sequence[Attendance]:
        result = [
            a for a in self._items if a.business_id == business_id and a.date == date_
        ]
        if employee_id is not None:
            result = [a for a in result if a.employee_id == employee_id]
        if status is not None:
            result = [a for a in result if a.status == status]
        return result

    async def list_by_employee(
        self,
        business_id: UUID,
        employee_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        status: AttendanceStatus | None = None,
    ) -> Sequence[Attendance]:
        result = [
            a
            for a in self._items
            if a.business_id == business_id and a.employee_id == employee_id
        ]
        if start_date is not None:
            result = [a for a in result if a.date >= start_date]
        if end_date is not None:
            result = [a for a in result if a.date <= end_date]
        if status is not None:
            result = [a for a in result if a.status == status]
        return sorted(result, key=lambda a: a.date)

    async def update(self, attendance: Attendance) -> None:
        for idx, a in enumerate(self._items):
            if (
                a.business_id == attendance.business_id
                and a.employee_id == attendance.employee_id
                and a.date == attendance.date
            ):
                self._items[idx] = attendance
                return

    async def delete(self, attendance: Attendance) -> None:
        self._items = [
            a
            for a in self._items
            if not (
                a.business_id == attendance.business_id
                and a.employee_id == attendance.employee_id
                and a.date == attendance.date
            )
        ]

    async def upsert_many(self, attendances: list[Attendance]) -> Sequence[Attendance]:
        results: list[Attendance] = []
        for attendance in attendances:
            existing_idx = next(
                (
                    i
                    for i, a in enumerate(self._items)
                    if a.business_id == attendance.business_id
                    and a.employee_id == attendance.employee_id
                    and a.date == attendance.date
                ),
                None,
            )
            if existing_idx is not None:
                self._items[existing_idx].status = attendance.status
                self._items[existing_idx].overtime_hours = attendance.overtime_hours
                results.append(self._items[existing_idx])
            else:
                self._items.append(attendance)
                results.append(attendance)
        return results


class InMemoryUnitOfWork(UnitOfWorkPort):
    def __init__(
        self,
        business_repo: InMemoryBusinessRepository,
        holiday_repo: InMemoryHolidayRepository,
        employee_repo: InMemoryEmployeeRepository,
        attendance_repo: InMemoryAttendanceRepository | None = None,
    ) -> None:
        self.businesses = business_repo
        self.holidays = holiday_repo
        self.employees = employee_repo
        self.attendance = attendance_repo or InMemoryAttendanceRepository()
        self.committed = False

    async def __aenter__(self) -> "InMemoryUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.committed = False


@pytest.fixture
def in_memory_business_repo(business_defaults) -> InMemoryBusinessRepository:
    business = Business.create(**business_defaults)
    return InMemoryBusinessRepository(items=[business])


@pytest.fixture
def in_memory_holiday_repo(
    in_memory_business_repo: InMemoryBusinessRepository,
) -> InMemoryHolidayRepository:
    business = in_memory_business_repo._items[0]
    holiday = Holiday.create(
        business_id=business.id,
        date_=date(2026, 1, 1),
        name="New Year's Day",
    )
    return InMemoryHolidayRepository(items=[holiday])


@pytest.fixture
def in_memory_employee_repo(
    in_memory_business_repo: InMemoryBusinessRepository,
) -> InMemoryEmployeeRepository:
    business = in_memory_business_repo._items[0]
    employee = Employee.create(
        id=uuid4(),
        business_id=business.id,
        name="John Doe",
        designation="Engineer",
        wage_type=WageType.MONTHLY,
        wage_rate=Decimal("50000.00"),
        working_hours_per_day=Decimal("8.0"),
        overtime_multiplier=Decimal("1.5"),
    )
    return InMemoryEmployeeRepository(items=[employee])


@pytest.fixture
def in_memory_attendance_repo() -> InMemoryAttendanceRepository:
    return InMemoryAttendanceRepository()


@pytest.fixture
def in_memory_uow(
    in_memory_business_repo: InMemoryBusinessRepository,
    in_memory_holiday_repo: InMemoryHolidayRepository,
    in_memory_employee_repo: InMemoryEmployeeRepository,
    in_memory_attendance_repo: InMemoryAttendanceRepository,
) -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork(
        business_repo=in_memory_business_repo,
        holiday_repo=in_memory_holiday_repo,
        employee_repo=in_memory_employee_repo,
        attendance_repo=in_memory_attendance_repo,
    )
