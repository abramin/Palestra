# Palestra (FitFlow) - Development Guide

## Project Overview

FitFlow is a booking and client management platform for personal trainers and fitness studios. See `docs/prd.md` for full product requirements.

## Architecture Overview

This project follows **Domain-Driven Design (DDD)** with **CQRS** and **Event-Driven Architecture**. The codebase is organized into distinct layers with strict boundaries.

```
src/
├── domain/           # Business logic, entities, value objects, domain events
├── application/      # Command/Query handlers, orchestration
├── infrastructure/   # External integrations, persistence, controllers
└── shared/           # Cross-cutting concerns (e.g., base classes)
```

---

## Architectural Guardrails & Ruleset

### 1. Layered Responsibilities

#### Domain Layer
- **Must contain all business logic**, invariants, and validations
- Entities and Value Objects must be **"rich"** (encapsulate behavior)
- No dependencies on infrastructure or application layers

#### Application Layer
- **Thin orchestrators** (Command/Query Handlers only)
- Responsible for:
  - Managing transactions via `UnitOfWork`
  - Side effects: Calling `repository.save()` and `event_bus.publish()`
  - Mapping between primitives and domain objects

#### Infrastructure Layer
- External integrations (Stripe, Kafka, Redis, etc.)
- Entry points (Controllers, CLI commands)
- Integration models should **mirror the external provider's API exactly**

---

### 2. Code Design Rules

#### Rich Models
- Attributes **must be private**
- Use expressive methods instead of setters:
  ```python
  # Good
  booking.cancel(reason=CancellationReason.CLIENT_REQUEST)

  # Bad
  booking.status = BookingStatus.CANCELLED
  ```

#### Value Objects
- Use them for data that requires **validation at creation**:
  ```python
  # Examples: Email, Price, Credits, SessionCapacity
  email = Email("user@example.com")  # Validates format
  price = Price(amount=50.00, currency="USD")  # Validates positive
  ```

#### No Message Chains (Avoid Lazy Loading)
```python
# Bad - ORM lazy loading creates hidden dependencies
user.bookings.filter(status='confirmed')

# Good - Explicit repository call
booking_repository.find_confirmed_by_user_id(user.id)
```

#### JSON Primitives at Boundaries
All **Commands, Queries, and Events** must use only:
- `str`, `int`, `float`, `bool`, `list`, `dict`, `None`

Convert complex types at the boundary:
```python
# Command definition
@dataclass
class CreateBookingCommand:
    session_id: str      # UUID converted to string
    user_id: str
    requested_at: str    # datetime as ISO string
```

---

### 3. Transactionality & Side Effects

#### Transaction Boundary
Must be in the **Application Layer** (Command Handler):
```python
class ConfirmHoldHandler:
    def handle(self, command: ConfirmHoldCommand) -> None:
        with self.__unit_of_work() as uow:
            hold = uow.holds.get(command.hold_id)
            booking = hold.confirm()
            uow.bookings.save(booking)
            uow.commit()

        # Events published AFTER transaction commits
        self.__event_bus.publish(booking.pull_events())
```

#### Pure Domain Services
Domain services must **NOT**:
- Save to repositories
- Publish events directly

They **must return** entities/events to the handler:
```python
# Domain service
class WaitlistPromotionService:
    def promote_next(self, session: Session, waitlist: List[WaitlistEntry]) -> Optional[SpotHold]:
        # Returns the hold, doesn't save it
        ...
```

#### Atomic Commands
**Never** execute a Query to decide how to build a Command. Commands must be **self-contained units of intent**.

---

### 4. CQRS (Command Query Responsibility Segregation)

#### Write Side - Repositories
- Use **only for fetching entities to modify them**
- Return domain entities
```python
class BookingRepository:
    def get(self, booking_id: BookingId) -> Booking: ...
    def save(self, booking: Booking) -> None: ...
```

#### Read Side - Finders
- Use for **fetching data for display/API responses**
- Must follow **SRP**: one class, one public `find()` method
- Must handle **pagination and filtering**
- Must return **ViewModels/QueryResponses**, not domain entities

```python
class UpcomingSessionsFinder:
    def find(self, query: UpcomingSessionsQuery) -> PaginatedResult[SessionViewModel]:
        # Returns DTOs optimized for the specific view
        ...
```

---

### 5. Event-Driven Patterns

#### Event Instantiation
Create events **inside the Domain** (Entities or Domain Services), never in the Application Layer:
```python
class Booking:
    def confirm(self) -> None:
        self.__status = BookingStatus.CONFIRMED
        self.__record(BookingConfirmedEvent(
            booking_id=str(self.id),
            session_id=str(self.session_id),
            user_email=self.user_email,
            session_name=self.session_name,
            starts_at=self.starts_at.isoformat()
        ))
```

#### Aggregate Roots
Use `record(event)` and `pull_events()` to manage events internally:
```python
class AggregateRoot:
    def __init__(self):
        self.__events: List[DomainEvent] = []

    def _record(self, event: DomainEvent) -> None:
        self.__events.append(event)

    def pull_events(self) -> List[DomainEvent]:
        events = self.__events.copy()
        self.__events.clear()
        return events
```

#### Event Context
Events must be **self-contained** - carry all necessary data, not just IDs:
```python
# Good - Self-contained
@dataclass
class BookingConfirmedEvent:
    booking_id: str
    user_email: str
    user_name: str
    session_name: str
    session_starts_at: str
    credits_used: int

# Bad - Requires back-filling queries
@dataclass
class BookingConfirmedEvent:
    booking_id: str  # Consumer must query for details
```

#### Requested Events
Use `...RequestedEvent` suffix for async side effects that bridge to future async commands:
```python
# Triggers async email sending
WelcomeEmailRequestedEvent(user_id=..., email=..., name=...)

# Triggers async payment processing
PaymentProcessingRequestedEvent(booking_id=..., amount=..., ...)
```

---

### 6. Error Handling

#### Preserve Tracebacks
```python
# Bad - Loses traceback
except SomeException as e:
    raise e

# Good - Preserves traceback
except SomeException:
    raise

# Good - Chain exceptions
except SomeException as e:
    raise DomainException("Context message") from e
```

#### Exception Hierarchy
```
DomainException (base)
├── BookingException
│   ├── SessionFullException
│   ├── HoldExpiredException
│   └── CancellationPolicyViolation
├── PaymentException
│   ├── InsufficientCreditsException
│   └── PaymentDeclinedException
└── ValidationException
    ├── InvalidEmailException
    └── InvalidCapacityException
```

---

### 7. Data Consistency

#### Foreign Keys
**Avoid DB-level foreign keys** on command-side replicas (replicated data from other services) to handle eventual consistency without failing consumers.

```python
# For replicated data from other bounded contexts:
# - No FK constraint
# - Handle missing references gracefully
# - Use eventual consistency patterns
```

#### Idempotency
All state-changing operations must be idempotent:
```python
class ConfirmHoldHandler:
    def handle(self, command: ConfirmHoldCommand) -> BookingId:
        # Check if already processed
        existing = self.__booking_repo.find_by_hold_id(command.hold_id)
        if existing:
            return existing.id

        # Process normally
        ...
```

---

## Testing Strategy

### Unit Tests
- Test domain logic in isolation
- No mocks for domain objects - use real instances
- Mock only infrastructure boundaries (repos, external services)

### Integration Tests
- Test Application Layer handlers with real database
- Use test containers for PostgreSQL, Redis
- Verify transaction boundaries work correctly

### Contract Tests
- Verify event schemas remain backward compatible
- Test external API integrations (Stripe, etc.)

---

## Quick Reference

| Layer | Contains | Can Depend On |
|-------|----------|---------------|
| Domain | Entities, VOs, Domain Events, Domain Services | Nothing (pure) |
| Application | Command/Query Handlers, DTOs | Domain |
| Infrastructure | Repos, Controllers, External APIs | Domain, Application |

| Pattern | Write Side | Read Side |
|---------|------------|-----------|
| Data Access | Repository | Finder |
| Returns | Domain Entity | ViewModel |
| Purpose | Modify state | Display data |

| Event Type | Suffix | Purpose |
|------------|--------|---------|
| Fact | `...Event` | Something happened |
| Intent | `...RequestedEvent` | Trigger async action |
