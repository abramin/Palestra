# Testing Philosophy: Inverted Pyramid

## The Traditional Pyramid (and why we invert it)

Traditional wisdom says: many unit tests, fewer integration tests, even fewer E2E tests.

**We invert this for Palestra because:**

1. **Correctness lives at boundaries.** A booking that validates in isolation but fails at the HTTP layer is worthless. A class session that persists correctly but cannot be queried is broken.

2. **Mocks lie.** A unit test with mocked dependencies proves your code works with your mock, not with the real system. Scheduling and booking flows fail at integration points—clock skew, transaction isolation, network partitions.

3. **Refactoring should be free.** If renaming a method breaks 50 unit tests but behavior is unchanged, your tests are testing implementation, not contracts.

4. **Business invariants span layers.** "A class cannot be overbooked" is not a unit-testable property—it requires HTTP parsing, storage lookup, and transaction boundaries working together.

---

## The Inverted Pyramid

```
        ┌─────────────────────────────────┐
        │     Feature / Contract Tests     │  ← Most tests here
        │   (Gherkin scenarios, OpenAPI)   │
        ├─────────────────────────────────┤
        │      Integration Tests           │  ← Hit real boundaries
        │  (HTTP, DB, adapters, timing)    │
        ├─────────────────────────────────┤
        │         Unit Tests               │  ← Fewest, must justify
        │   (Invariants, pure domain)      │
        └─────────────────────────────────┘
```

---

## When to write each type

### Feature / Contract Tests (default)

**Write these first. They are the source of truth.**

Feature tests answer: "Does the system behave correctly from a user's perspective?"

**Use for:**

- Every user-visible behavior (class template creation, session scheduling, booking creation)
- Every state transition in the domain (session scheduled → active → canceled)
- Every error the user can observe (class full, missing credits, invalid timeslot)
- API contract compliance (request/response behavior)

**Format:** Gherkin scenarios in `.feature` files

```gherkin
Scenario: Booking cannot be created when class is full
  Given a class session with capacity 10
  And 10 confirmed bookings exist
  When a user tries to book the session
  Then the response status is 409
  And the error is "class_full"
```

**The test:**

- Hits real HTTP endpoints
- Uses real database
- Exercises real capacity and credit validation

**Not mocked:** Storage, crypto, time (use test clock, not mock clock)

---

### Integration Tests (for what features can't cover)

Integration tests answer: "Do the components work together under stress, timing, and failure conditions?"

**Use for:**

- Concurrency (parallel booking requests, race to cancel)
- Timing (session start time, cancellation windows, TTL boundaries)
- Partial failure (DB timeout mid-booking, network partition)
- Retry behavior (idempotency under duplicate requests)
- Shutdown (graceful drain, in-flight request handling)
- Cache coherence (invalidation timing, stampede protection)

**Format:** Pytest suites with real infrastructure

```go
def test_concurrent_booking_does_not_overbook(db, api_client):
    # Hit real HTTP, real DB, real booking store
    # Assert capacity is not exceeded under parallel requests
    ...
```

**Why not feature tests?** Gherkin can't express "50 concurrent requests" or "kill the DB connection mid-write" cleanly.

**Not mocked:** Infrastructure. Use testcontainers or embedded stores.

---

### Unit Tests (exceptional, must justify)

Unit tests answer: "Does this specific invariant hold in isolation?"

**The justification question:** _"What invariant breaks if this test is removed, and why can't an integration test catch it?"_

**Use for:**

- **Pure domain logic** that is computationally complex
  - Schedule recurrence parsing and matching
  - Credit deduction rules
  - Booking overlap detection
- **Invariants unreachable via integration**
  - Edge cases in date/time parsing (malformed input variations)
  - State machine transitions that require specific setup
- **Error mapping at boundaries**
  - Domain error → HTTP status mapping
  - Store sentinel → domain error translation

**Format:** Pytest suites, no mocks of domain types

```go
def test_credit_deduction_rules():
    granted = Credits(10)
    requested = Credits(8)
    assert granted.can_cover(requested)

    granted = Credits(5)
    requested = Credits(8)
    assert not granted.can_cover(requested)
```

**Why unit here?** Pure function, many edge cases, no I/O involved. Integration test would just add noise.

---

## Decision flowchart

```
Is this user-visible behavior?
    ├─ Yes → Feature test (Gherkin)
    └─ No ↓

Is this about concurrency, timing, failure, or shutdown?
    ├─ Yes → Integration test
    └─ No ↓

Is this a pure domain invariant with many edge cases?
    ├─ Yes → Unit test (justify in comment)
    └─ No ↓

Is this error mapping at a boundary?
    ├─ Yes → Unit test (justify in comment)
    └─ No ↓

Do you actually need a test?
    └─ Maybe the feature test already covers it.
```

---

## What we don't test (or test minimally)

### No tests for:

- Dataclass field existence (type checker/linter catches this)
- Constructor calls with valid input (feature tests cover happy path)
- "Does the mock return what I told it to" (tautology)
- Third-party library behavior (trust or vendor)

### Minimal tests for:

- HTTP handler routing (one test per route to prove wiring, not logic)
- Store CRUD (one test per operation type, not per entity)
- Config parsing (one test proving it loads, not every field)

---

## Mock policy

**Mocks are allowed only to induce failure modes.**

| Scenario                                  | Mock allowed? | Why                                      |
| ----------------------------------------- | ------------- | ---------------------------------------- |
| Test happy path booking creation          | ❌            | Use real store, real capacity checks     |
| Test behavior when DB is down             | ✅            | Need to simulate unavailability          |
| Test behavior when external payment times out | ✅        | Can't reliably make real provider timeout |
| Test capacity/credit validation logic     | ❌            | Use real rules, real validators          |
| Test retry on transient failure           | ✅            | Need to control failure/success sequence |

**Never mock:**

- Domain types (entities, value objects, aggregates)
- Time (use test clock that you control, not mock)
- Crypto (use real crypto with test keys)
- The thing you're testing

---

## Test naming reflects this philosophy

Tests are named for **behavior**, not **implementation**:

```go
// ❌ Implementation-coupled (breaks on refactor)
func TestTokenService_ValidateToken() { ... }
func TestTokenStore_FindByJTI() { ... }

// ✅ Behavior-coupled (survives refactor)
func TestTokenValidation_RejectsExpiredTokens() { ... }
func TestTokenValidation_RejectsRevokedTokens() { ... }
func TestTokenValidation_AcceptsValidTokenWithRequiredScopes() { ... }
```

---

## Coverage philosophy

**We don't target a coverage percentage.** Coverage is a signal, not a goal.

Instead, we target:

- **100% of user-visible behaviors** have feature tests
- **100% of documented error codes** are exercised by tests
- **100% of state transitions** are tested (can enter, can exit, no trapdoors)
- **Every security invariant** has at least one test that would fail if violated

Low coverage in a file might mean:

- Dead code (delete it)
- Trivial code (acceptable)
- Missing tests (investigate)

High coverage with bad tests is worse than low coverage with good tests.

---

## Relationship to agents

| Agent                | Testing implication                                                     |
| -------------------- | ----------------------------------------------------------------------- |
| **QA**               | Every CONTRACT finding becomes a feature scenario                       |
| **Secure-by-design** | Every SECURITY invariant gets a test proving enforcement                |
| **DDD**              | Pure domain logic may warrant unit tests for complex invariants         |
| **Balance**          | EFFECTS violations ("scattered I/O") make testing hard—fix design first |
| **Performance**      | Load test scenarios validate PERFORMANCE assumptions                    |
| **Testing**          | Translates all of the above into actual test code                       |

---

## Summary

1. **Feature tests are the default.** If it's user-visible, it's a Gherkin scenario.
2. **Integration tests cover the hard parts.** Concurrency, timing, failure, shutdown.
3. **Unit tests are exceptional.** Every one must answer: "What invariant, and why not integration?"
4. **Mocks induce failures only.** Happy paths use real components.
5. **Name tests for behavior.** Refactoring should not break tests.
6. **Coverage is a signal, not a target.** Behaviors covered matters more than lines covered.
