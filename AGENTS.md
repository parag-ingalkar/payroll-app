## Purpose

This project uses a Clean Architecture / Vertical Slice pattern with FastAPI, SQLAlchemy (async), and Postgres. The goal of this document is to define how AI coding agents should work within this structure, so they can:

- Implement a full vertical slice (domain → application → infrastructure → presentation) from scratch.
- Write unit and integration tests that match our existing patterns.
- Ask the right domain questions before generating code.
- First create a plan for implementation. Once it is approved by me, only then modify any code in the codebase.

This file is the contract between humans and agents about how code should be structured and what invariants must hold.

Businesses employing fewer than 10 workers spend hours each month manually calculating employee salaries factoring in variable elements like paid leave, unpaid absences, overtime hours, and festival bonuses because payroll software is designed for larger organizations and doesn't offer one-click processing for tiny teams.
The project is a fullstack application solution to this problem statement. It is focused for MSEs in India.

## Architectural Overview

### Layers

Each “slice” (Business, Holidays, Employees, etc.) has the same high-level structure:

- `app/<slice>/domain/`
  - Entities, value objects
  - Domain exceptions
- `app/<slice>/application/`
  - Commands (dataclasses)
  - Use cases (application services)
  - Ports (repository interfaces)
- `app/<slice>/infrastructure/`
  - ORM models (SQLAlchemy)
  - Repository implementations
- `app/<slice>/presentation/`
  - Pydantic schemas
  - FastAPI router
  - Exception handlers

Cross-cutting:

- `app/core/uow.py` – `SqlAlchemyUnitOfWork` and `UnitOfWorkPort`.
- `app/core/db.py` – async engine/session factory.
- `app/core/dependencies.py` – auth stub (`get_current_user`).
- `app/core/exception_handler.py` – central registration of slice exception handlers.

### Clean architecture principles

- Domain layer should not depend on application, infrastructure, or presentation.
- Application depends on domain and ports (including `UnitOfWorkPort`).
- Infrastructure implements ports; it depends on domain and application ports.
- Presentation depends on application and domain, never directly on infrastructure.

## Ownership / Authorization

### Rule

- Every `Business` has an `owner_id`.
- All slices that operate under a business (Holidays, Employees, etc.) must enforce: **only the owner can perform operations** on that business.

### Enforcement

- Application commands that address a business must include:

  ```python
  business_id: UUID
  owner_id: str
  ```

- At the start of each use case:

  ```python
  business = await uow.businesses.get_by_id_and_owner(
      business_id=cmd.business_id,
      owner_id=cmd.owner_id,
  )
  if business is None:
      raise BusinessNotFoundError(
          f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
      )
  ```

- Repositories do **not** perform ownership checks; they expose methods like:

  ```python
  async def get_by_id_and_owner(...) -> Business | None
  ```

- Routers never take `owner_id` from the client; they get it from the auth stub:

  ```python
  current_user: CurrentPrincipal = Depends(get_current_user)
  cmd = SomeCommand(
      business_id=business_id_from_path,
      owner_id=current_user.clerk_user_id,
      ...
  )
  ```

The Employees slice must follow exactly this pattern.

## Repositories and Unit of Work

### Ports

- Repository ports live in `app/<slice>/application/ports.py`.
- They are pure interfaces, e.g.:

  ```python
  class EmployeeRepositoryPort(Protocol):
      async def add(self, employee: Employee) -> None: ...
      async def get_by_business_and_id(
          self, business_id: UUID, employee_id: UUID
      ) -> Employee | None: ...
      async def list_by_business(...) -> Sequence[Employee]: ...
      ...
  ```

### SQLAlchemy repositories

- ORM models have `from_entity` / `to_entity` methods in the infrastructure layer:

  ```python
  class EmployeeModel(Base):
      ...

      @classmethod
      def from_entity(cls, employee: Employee) -> "EmployeeModel": ...
      def to_entity(self) -> Employee: ...
  ```

- The repository uses these:

  ```python
  class SqlAlchemyEmployeeRepository(EmployeeRepositoryPort):
      def __init__(self, session: AsyncSession) -> None:
          self.session = session

      async def add(self, employee: Employee) -> None:
          model = EmployeeModel.from_entity(employee)
          self.session.add(model)
          # commit is done in UoW

      async def get_by_business_and_id(...) -> Employee | None:
          result = await self.session.execute(...)
          model = result.scalar_one_or_none()
          return model.to_entity() if model else None
  ```

### Unit of Work

- The SQLAlchemy UoW provides repositories as attributes:

  ```python
  class SqlAlchemyUnitOfWork(UnitOfWorkPort):
      def __init__(self, session_factory):
          self._session_factory = session_factory

      async def __aenter__(self):
          self.session = self._session_factory()
          self.businesses = SqlAlchemyBusinessRepository(self.session)
          self.holidays = SqlAlchemyHolidayRepository(self.session)
          self.employees = SqlAlchemyEmployeeRepository(self.session)  # new slice
          return self

      async def __aexit__(self, exc_type, exc, tb):
          ...

      async def commit(self) -> None:
          await self.session.commit()
  ```

- Use cases use:

  ```python
  async with self.uow as uow:
      ...  # operations on uow.businesses / uow.employees
      await uow.commit()
  ```

## Domain Logic and Validation

- Domain entities encapsulate invariants and normalization logic.
- Example used for Holidays:

  ```python
  class Holiday:
      ...
      def rename(self, new_name: str) -> None:
          normalized = new_name.strip()
          self.name = normalized or None
  ```

- Pydantic schemas handle request-time validation and normalization (e.g., trimming strings, rejecting invalid formats).
- Domain exceptions signal business rule violations, e.g.:

  - `HolidayAlreadyExistsError`
  - `HolidayNotFoundError`
  - For Employees: plan `EmployeeNotFoundError`, `EmployeeAlreadyExistsError`, etc.

## Pydantic Schemas (Presentation Layer)

- Use Pydantic v2, `model_config = ConfigDict(from_attributes=True)` for read models.
- Separate schemas:

  - `EmployeeCreate` – required fields for creation.
  - `EmployeeUpdate` – optional fields for PATCH.
  - `EmployeeRead` – fields returned to clients.

- For PATCH semantics:

  - Use `model_fields_set` to detect whether a field was provided:

    ```python
    if "name" not in payload.model_fields_set and "title" not in payload.model_fields_set:
        raise HTTPException(400, "No fields to update")
    ```

  - Use field validators to normalize inputs:

    ```python
    class HolidayUpdate(BaseModel):
        name: str | None = Field(default=None, max_length=100)

        @field_validator("name")
        @classmethod
        def normalize_name(cls, v):
            if v is None:
                return None
            s = v.strip()
            return s or None
    ```

  - Employees should follow identical patterns for string fields (e.g., names, titles).

## Routers

- One router per slice, mounted under `/businesses/{business_id}/<slice>`.

- Example pattern (Holidays; Employees should mirror):

  ```python
  @router.post(
      "",
      response_model=HolidayRead,
      status_code=status.HTTP_201_CREATED,
  )
  async def create_holiday(
      business_id: UUID,
      payload: HolidayCreate,
      current_user: CurrentPrincipal = Depends(get_current_user),
      use_case: CreateHolidayUseCase = Depends(get_create_holiday_use_case),
  ) -> HolidayRead:
      cmd = CreateHolidayCommand(
          business_id=business_id,
          owner_id=current_user.clerk_user_id,
          date=payload.date,
          name=payload.name,
      )
      holiday = await use_case.execute(cmd)
      return HolidayRead.model_validate(holiday)
  ```

- PATCH endpoints:

  - Reject empty payloads with 400.
  - Use `model_fields_set` and normalized fields.
  - Let use case handle “not found” via domain exception; router may map to 404 or rely on global handler.

- DELETE endpoints:

  - Return 204 on success.
  - For non-existent resources, either no-op or raise domain exception and handle via exception handler.

## Exception Handling

- Central function:

  ```python
  # app/core/exception_handler.py
  from app.business.presentation.exception_handler import register_business_exception_handlers
  from app.holidays.presentation.exception_handler import register_holiday_exception_handlers
  from app.employees.presentation.exception_handler import register_employee_exception_handlers

  def register_exception_handlers(app):
      register_business_exception_handlers(app)
      register_holiday_exception_handlers(app)
      register_employee_exception_handlers(app)
  ```

- `app/main.py`:

  ```python
  app = FastAPI(title="Easy Payroll API")

  register_exception_handlers(app)

  app.include_router(business_router)
  app.include_router(holidays_router)
  app.include_router(employees_router)
  ```

- Slice-level exception handlers map domain errors to HTTP responses with structured JSON, e.g.:

  ```python
  @app.exception_handler(EmployeeAlreadyExistsError)
  async def employee_already_exists_exception_handler(...):
      return JSONResponse(
          status_code=409,
          content={
              "detail": {
                  "code": "employee_already_exists",
                  "message": str(exc) or "...",
                  "fields": ["some_field"],
              }
          },
      )
  ```

## Testing Strategy

### Unit tests

- Located under `tests/unit/...`.
- Use in-memory repositories and `InMemoryUnitOfWork`:

  - `InMemoryBusinessRepository`
  - `InMemoryHolidayRepository`
  - `InMemoryEmployeeRepository` (to add)

- Fixtures:

  - `business_defaults`, `holiday_defaults`, `employee_defaults` (Employee to add) define baseline data.
  - Business and slice entities are seeded with consistent `business_id` and `owner_id`.

- Tests for use cases:

  - Happy paths: correct creation / update / delete.
  - Ownership: wrong owner → `BusinessNotFoundError`.
  - Duplicate / not found: appropriate domain error raised.
  - Ensure `uow.committed` is `True`/`False` as expected.

### Integration tests

- Located under `tests/integration/...`.
- Use `api_client` fixture that overrides `get_session_factory` for the whole app.
- Seed via **HTTP**:

  - Use Business router (`POST /businesses`) to create business before hitting Holidays/Employees.
  - No direct seeding via UoW in router tests (to avoid transaction mismatches).

- For each slice:

  - Test basic CRUD flows via HTTP.
  - Test ownership (wrong business id → `business_not_found`).
  - Test domain error mapping (duplicate → 409, not found → 404, invalid input → 400).


## Code quality verification

- Ensure the backend code is linted and formatted correctly. Run the following commands from the backend directory to verify:
  - Ruff check: "uv run ruff check"
  - Fix with: "uv run ruff check --fix"
  - Ruff format: "uv run ruff format"
  - Pyright import checks: "uv run pyright"

## Alembic migration scripts

- Generate migration scripts when new orm models are added. Follow these steps:
  - Import the model in `backend/alembic/env.py`
  eg. `from app.holidays.infrastructure.orm import HolidayModel  # noqa: F401 - ensure models are imported for Alembic's autogenerate`
  - Run `uv run alembic -m "<short descriptive message>" --autogenerate`
  eg. `uv run alembic -m "add holidays table" --autogenerate`
