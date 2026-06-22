## Skill: `vertical_slice_tests`

**Goal:** Create unit and integration tests for a vertical slice (existing or newly added) following the current testing conventions.

**Inputs the agent must gather:**

1. **Domain behavior requirements:**
   - What behaviors / invariants must be tested?
   - What error conditions (e.g., duplicates, not found, invalid input)?

2. **Existing slice references:**
   - Which existing slice’s tests to mirror (usually Business or Holidays)?

3. **Persistence expectations:**
   - Which operations must be observable in the DB (integration tests)?
   - What data shape do we expect after operations?

**What the agent should produce:**

1. **Unit tests:**

   Under `tests/unit/application/`:

   - A `conftest.py` extension if necessary:
     - `InMemory<Aggregate>Repository`.
     - Updated `InMemoryUnitOfWork` with `.employees` or other slice repo.
     - Default fixtures for the new slice (`<slice>_defaults`).

   - Tests like `test__<slice>_use_cases.py`:

     - Happy paths:
       - Create, list, get, update, delete.
     - Ownership:
       - Wrong `owner_id` → `BusinessNotFoundError`.
     - Domain errors:
       - Duplicate entity → `<Slice>AlreadyExistsError`.
       - Missing entity → `<Slice>NotFoundError`.

2. **Integration tests (SQLAlchemy use cases):**

   Under `tests/integration/`:

   - `test__<slice>_sqlalchemy.py`:

     - Use `sqlalchemy_uow` fixture.
     - Seed Business via DB or fixture.
     - Use use cases directly to verify:
       - Correct DB writes.
       - Filtering logic (e.g., by year/month equivalent for employees if any).
       - Error behavior.

3. **Integration tests (Routers):**

   Under `tests/integration/`:

   - `test__<slice>_router.py`:

     - Use `api_client` fixture.
     - Seed Business via `POST /businesses` (match Business router tests).
     - Exercise all routes:
       - POST /businesses/{business_id}/<slice>
       - GET /businesses/{business_id}/<slice>
       - GET /businesses/{business_id}/<slice>/{id or key}
       - PATCH /businesses/{business_id}/<slice>/{id or key}
       - DELETE /businesses/{business_id}/<slice>/{id or key}
     - Assert:
       - Ownership enforcement (wrong business id → `business_not_found` code).
       - Domain error mapping for duplicates, invalid data, not found.

**Constraints:**

- Tests must not seed data via a different session/transaction than the app uses in router tests; all router seeding must go through HTTP.
- Unit tests must use in-memory repos and UoW, not real DB.
- Test naming should follow the existing style: `test__<description>`.
