## Skill: `vertical_slice_implementation`

**Goal:** Implement a full vertical slice (domain, application, infrastructure, presentation) for a new feature (e.g., Employees) following the project’s Clean Architecture and ownership rules.

**Inputs the agent must gather:**

Before generating code, the agent must ask and clarify:

1. **Domain concepts:**
   - What is the new aggregate entity (e.g., Employee)?
   - What are its key attributes (types, required vs optional)?
   - What invariants or business rules must hold (e.g., name non-empty, unique employee id per business, status transitions, etc.)?

2. **Operations / use cases:**
   - Which operations do we need?
     - Typically: create, list, get-by-id, update (PATCH), delete.
   - Are there any special operations (e.g., “activate/deactivate employee”)?

3. **Constraints & relationships:**
   - How does this entity relate to Business (one-to-many? unique constraints)?
   - Do we enforce ownership via `owner_id` similarly to Holidays?

4. **API design:**
   - Expected HTTP endpoints (paths under `/businesses/{business_id}/...`).
   - Request/response shapes and any special filters.

**What the agent should produce:**

1. **Domain layer:**
   - `app/<slice>/domain/entities.py` – main entity class with factory methods and behavior methods (e.g., `Employee.create`, `activate`, `rename`).
   - `app/<slice>/domain/exceptions.py` – slice-specific exceptions.

2. **Application layer:**
   - `app/<slice>/application/commands.py`:
     - Commands like `Create<Aggregate>Command`, `List<Aggregate>Command`, `Update<Aggregate>Command`, `Delete<Aggregate>Command`, including `business_id` and `owner_id`.
   - `app/<slice>/application/ports.py`:
     - Repository port interface.
   - `app/<slice>/application/use_cases.py`:
     - Use cases implementing the commands, following the same patterns as Business/Holidays:
       - Ownership check via `uow.businesses.get_by_id_and_owner`.
       - Use `uow.<slice_repo>` for persistence.
       - Raise domain errors for business conditions.
       - Commit via `uow.commit()`.

3. **Infrastructure layer:**
   - `app/<slice>/infrastructure/orm.py`:
     - SQLAlchemy model with foreign key to `BusinessModel`.
     - Relationships using string references to avoid circular imports.
     - `from_entity` / `to_entity` methods.
   - `app/<slice>/infrastructure/repository.py`:
     - `SqlAlchemy<Aggregate>Repository` implementing the port.

4. **Presentation layer:**
   - `app/<slice>/presentation/schemas.py`:
     - Create/Update/Read schemas using Pydantic v2.
   - `app/<slice>/presentation/dependencies.py`:
     - Factory functions wiring use cases with `SqlAlchemyUnitOfWork` via `get_uow`.
   - `app/<slice>/presentation/router.py`:
     - Routes under `/businesses/{business_id}/<slice>` mirroring Holidays.
     - Use `CurrentPrincipal` for `owner_id`.

5. **Exception handling:**
   - `app/<slice>/presentation/exception_handler.py`:
     - Handlers mapping slice domain exceptions to proper HTTP responses.

6. **Integration wiring:**
   - Update `app/core/uow.SqlAlchemyUnitOfWork` to include new repo.
   - Update `app/core/exception_handler.register_exception_handlers` to include slice handler.
   - Update `app/main.py` to include the new router.

**Constraints:**

- Must not bypass auth/ownership rules.
- Must not introduce cross-layer or cross-slice dependencies in the wrong direction.
- Must keep naming and patterns consistent with Business and Holidays.
