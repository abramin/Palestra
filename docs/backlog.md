# FitFlow Backlog

> Issues structured as **thin vertical slices** following the [Architecture Guide](../CLAUDE.md).
> Each issue delivers end-to-end functionality across Domain → Application → Infrastructure layers.

---

## Milestone 1: Foundation

### Issue: Project Structure + Layer Setup
**Priority:** P0 | **Estimate:** Setup

**Description:**
Set up the project structure following DDD layered architecture.

**Acceptance Criteria:**
- [ ] Create directory structure:
  ```
  src/
  ├── domain/
  │   ├── __init__.py
  │   ├── shared/          # Base classes
  │   ├── booking/         # Booking bounded context
  │   ├── scheduling/      # Session/Template context
  │   └── membership/      # Credits/Membership context
  ├── application/
  │   ├── __init__.py
  │   ├── booking/
  │   ├── scheduling/
  │   └── membership/
  └── infrastructure/
      ├── __init__.py
      ├── persistence/     # Repositories, Django models
      ├── api/             # Controllers/Views
      └── external/        # Stripe, Redis, etc.
  ```
- [ ] Create base classes in `domain/shared/`:
  - `Entity` - base with ID and equality
  - `AggregateRoot` - with `_record(event)` and `pull_events()`
  - `ValueObject` - immutable with equality by value
  - `DomainEvent` - base event class
- [ ] Create base classes in `application/`:
  - `Command` / `Query` dataclasses (JSON primitives only)
  - `CommandHandler` / `QueryHandler` protocols
  - `UnitOfWork` protocol
- [ ] Docker Compose with PostgreSQL and Redis
- [ ] Basic Django settings pointing to new structure

---

### Issue: User Registration (Vertical Slice)
**Priority:** P0 | **Estimate:** Small

**Description:**
Implement user registration as a complete vertical slice demonstrating the architecture.

**Acceptance Criteria:**

**Domain Layer (`domain/membership/`):**
- [ ] `Email` Value Object - validates format at creation
- [ ] `Password` Value Object - validates strength, hashes value
- [ ] `User` Entity - rich model with private attributes
- [ ] `UserRegisteredEvent` - self-contained (includes email, name, registered_at)

**Application Layer (`application/membership/`):**
- [ ] `RegisterUserCommand` - primitives only (email: str, password: str, name: str)
- [ ] `RegisterUserHandler`:
  ```python
  def handle(self, command: RegisterUserCommand) -> str:
      with self.__unit_of_work() as uow:
          email = Email(command.email)
          user = User.create(email, Password(command.password), command.name)
          uow.users.save(user)
          uow.commit()
      self.__event_bus.publish(user.pull_events())
      return str(user.id)
  ```

**Infrastructure Layer (`infrastructure/`):**
- [ ] `UserRepository` - implements save/get
- [ ] `POST /api/v1/auth/register` endpoint
- [ ] Django ORM model mapped to User entity

**Tests:**
- [ ] Unit tests for Email, Password validation
- [ ] Integration test for RegisterUserHandler
- [ ] API test for registration endpoint

---

### Issue: JWT Authentication
**Priority:** P0 | **Estimate:** Small

**Description:**
Implement JWT-based authentication following the architecture.

**Acceptance Criteria:**

**Domain Layer:**
- [ ] `AuthToken` Value Object
- [ ] `UserAuthenticatedEvent` (user_id, email, authenticated_at)

**Application Layer:**
- [ ] `AuthenticateUserCommand` (email: str, password: str)
- [ ] `AuthenticateUserHandler` - validates credentials, returns token
- [ ] `RefreshTokenCommand` / `RefreshTokenHandler`

**Infrastructure Layer:**
- [ ] `POST /api/v1/auth/login` - returns JWT tokens
- [ ] `POST /api/v1/auth/refresh` - refreshes access token
- [ ] JWT middleware for protected routes

---

## Milestone 2: Scheduling Context

### Issue: Class Template Management (Vertical Slice)
**Priority:** P1 | **Estimate:** Medium

**Description:**
Trainers can create and manage class templates (e.g., "Morning Yoga - 60min, max 12 people").

**Acceptance Criteria:**

**Domain Layer (`domain/scheduling/`):**
- [ ] `Duration` Value Object - validates positive minutes
- [ ] `Capacity` Value Object - validates positive integer
- [ ] `ClassTemplate` Entity:
  ```python
  class ClassTemplate(AggregateRoot):
      def __init__(self, ...):
          self.__name: str
          self.__duration: Duration
          self.__default_capacity: Capacity
          self.__trainer_id: UserId

      @classmethod
      def create(cls, name, duration, capacity, trainer_id) -> "ClassTemplate":
          template = cls(...)
          template._record(ClassTemplateCreatedEvent(...))
          return template

      def update(self, name, duration, capacity) -> None:
          # Update logic with validation
          self._record(ClassTemplateUpdatedEvent(...))
  ```

**Application Layer (`application/scheduling/`):**
- [ ] `CreateClassTemplateCommand` (name: str, duration_minutes: int, capacity: int, trainer_id: str)
- [ ] `CreateClassTemplateHandler`
- [ ] `UpdateClassTemplateCommand` / `UpdateClassTemplateHandler`
- [ ] `GetClassTemplatesQuery` (trainer_id: str | None, page: int, page_size: int)
- [ ] `ClassTemplatesFinder` - returns `ClassTemplateViewModel` (not entities)

**Infrastructure Layer:**
- [ ] `ClassTemplateRepository`
- [ ] `ClassTemplatesFinder` (read-side, returns ViewModels)
- [ ] CRUD endpoints: `GET/POST /api/v1/templates`, `GET/PUT/DELETE /api/v1/templates/{id}`
- [ ] Permission: trainers manage own templates, admins manage all

---

### Issue: Session Scheduling (Vertical Slice)
**Priority:** P1 | **Estimate:** Medium

**Description:**
Create actual sessions from templates with specific dates/times.

**Acceptance Criteria:**

**Domain Layer (`domain/scheduling/`):**
- [ ] `SessionStatus` enum (draft, published, in_progress, completed, cancelled)
- [ ] `TimeSlot` Value Object (starts_at, ends_at) - validates end > start
- [ ] `ClassSession` Entity:
  ```python
  class ClassSession(AggregateRoot):
      def publish(self) -> None:
          if self.__status != SessionStatus.DRAFT:
              raise InvalidSessionStateException()
          self.__status = SessionStatus.PUBLISHED
          self._record(SessionPublishedEvent(...))

      def cancel(self, reason: str) -> None:
          # Rich behavior with event recording
  ```
- [ ] `SessionPublishedEvent`, `SessionCancelledEvent` - self-contained

**Application Layer:**
- [ ] `CreateSessionCommand` (template_id: str | None, trainer_id: str, starts_at: str, ends_at: str, capacity: int)
- [ ] `PublishSessionCommand` (session_id: str)
- [ ] `CancelSessionCommand` (session_id: str, reason: str)
- [ ] Handlers for each command
- [ ] `GetUpcomingSessionsQuery` (from_date: str, to_date: str, trainer_id: str | None)
- [ ] `UpcomingSessionsFinder` - read-side with pagination

**Infrastructure Layer:**
- [ ] `SessionRepository`
- [ ] `UpcomingSessionsFinder` (returns `SessionViewModel` with availability)
- [ ] Endpoints with proper filtering

---

## Milestone 3: Booking Context

### Issue: Create Booking with Capacity Check (Vertical Slice)
**Priority:** P1 | **Estimate:** Medium

**Description:**
Users can book sessions with database-level capacity enforcement.

**Acceptance Criteria:**

**Domain Layer (`domain/booking/`):**
- [ ] `BookingStatus` enum (confirmed, cancelled, no_show)
- [ ] `Booking` Entity:
  ```python
  class Booking(AggregateRoot):
      @classmethod
      def create(cls, session_id, user_id, user_email, session_name, starts_at) -> "Booking":
          booking = cls(...)
          booking._record(BookingConfirmedEvent(
              booking_id=str(booking.id),
              session_id=str(session_id),
              user_email=user_email,        # Self-contained!
              session_name=session_name,    # No back-filling needed
              starts_at=starts_at.isoformat()
          ))
          return booking
  ```
- [ ] `BookingConfirmedEvent` - self-contained with all context

**Application Layer:**
- [ ] `CreateBookingCommand` (session_id: str, user_id: str)
- [ ] `CreateBookingHandler`:
  ```python
  def handle(self, command: CreateBookingCommand) -> str:
      with self.__unit_of_work() as uow:
          session = uow.sessions.get_with_lock(command.session_id)  # SELECT FOR UPDATE

          if session.is_full():
              raise SessionFullException(session.available_spots)

          user = uow.users.get(command.user_id)
          booking = Booking.create(
              session.id, user.id, user.email,
              session.name, session.starts_at
          )

          uow.bookings.save(booking)
          uow.commit()

      self.__event_bus.publish(booking.pull_events())
      return str(booking.id)
  ```
- [ ] `GetUserBookingsQuery` / `UserBookingsFinder`

**Infrastructure Layer:**
- [ ] `BookingRepository` with `save()`, `get()`
- [ ] `UserBookingsFinder` - read-side for "My Bookings" view
- [ ] `POST /api/v1/sessions/{id}/book` endpoint
- [ ] Row locking via `select_for_update()` in repository
- [ ] Return 409 Conflict when full

**Tests:**
- [ ] Concurrent booking tests (race condition prevention)
- [ ] Capacity enforcement tests

---

### Issue: Cancel Booking with Refund Policy (Vertical Slice)
**Priority:** P1 | **Estimate:** Small

**Description:**
Users can cancel bookings with time-based refund policy.

**Acceptance Criteria:**

**Domain Layer:**
- [ ] `CancellationPolicy` Domain Service (pure - no side effects):
  ```python
  class CancellationPolicy:
      def calculate_refund(self, booking: Booking, cancelled_at: datetime) -> RefundResult:
          hours_before = (booking.starts_at - cancelled_at).total_seconds() / 3600
          if hours_before > 24:
              return RefundResult(percentage=100)
          elif hours_before > 12:
              return RefundResult(percentage=50)
          else:
              return RefundResult(percentage=0)
  ```
- [ ] `Booking.cancel()` method - records `BookingCancelledEvent`
- [ ] `BookingCancelledEvent` - includes refund_percentage, user_email, session_name

**Application Layer:**
- [ ] `CancelBookingCommand` (booking_id: str, user_id: str)
- [ ] `CancelBookingHandler` - uses CancellationPolicy, calls booking.cancel()

**Infrastructure Layer:**
- [ ] `PATCH /api/v1/bookings/{id}/cancel`
- [ ] Owner or admin permission check

---

### Issue: Spot Hold System (Vertical Slice)
**Priority:** P2 | **Estimate:** Medium

**Description:**
Implement temporary 10-minute holds before booking confirmation (prevents race conditions in UI).

**Acceptance Criteria:**

**Domain Layer (`domain/booking/`):**
- [ ] `HoldStatus` enum (pending, confirmed, expired)
- [ ] `SpotHold` Entity:
  ```python
  class SpotHold(AggregateRoot):
      def confirm(self) -> Booking:
          if self.__status != HoldStatus.PENDING:
              raise HoldExpiredException()
          if self.is_expired():
              raise HoldExpiredException()

          self.__status = HoldStatus.CONFIRMED
          return Booking.create_from_hold(self)

      def is_expired(self) -> bool:
          return datetime.utcnow() > self.__expires_at
  ```

**Application Layer:**
- [ ] `CreateHoldCommand` (session_id: str, user_id: str)
- [ ] `ConfirmHoldCommand` (hold_id: str)
- [ ] `CreateHoldHandler` - checks capacity including active holds
- [ ] `ConfirmHoldHandler` - converts hold to booking

**Infrastructure Layer:**
- [ ] Redis for hold TTL tracking
- [ ] `POST /api/v1/sessions/{id}/hold` - creates 10-min hold
- [ ] `POST /api/v1/holds/{id}/confirm` - converts to booking
- [ ] `DELETE /api/v1/holds/{id}` - releases hold

---

### Issue: Waitlist with Auto-Promotion (Vertical Slice)
**Priority:** P2 | **Estimate:** Medium

**Description:**
Users can join waitlist for full sessions; auto-promoted when spots open.

**Acceptance Criteria:**

**Domain Layer:**
- [ ] `WaitlistEntry` Entity with position
- [ ] `WaitlistPromotionService` (pure domain service):
  ```python
  class WaitlistPromotionService:
      def promote_next(self, session: Session, waitlist: List[WaitlistEntry]) -> Optional[SpotHold]:
          """Returns a hold for the next waitlist member, or None if empty."""
          if not waitlist:
              return None

          next_entry = min(waitlist, key=lambda e: e.position)
          hold = SpotHold.create_from_waitlist(
              session_id=session.id,
              user_id=next_entry.user_id,
              expires_in_minutes=5  # Priority hold
          )
          return hold
  ```
- [ ] `WaitlistPromotedEvent` - self-contained (user_email, session_name, etc.)

**Application Layer:**
- [ ] `JoinWaitlistCommand` / `JoinWaitlistHandler`
- [ ] `LeaveWaitlistCommand` / `LeaveWaitlistHandler`
- [ ] Event handler: On `BookingCancelledEvent`, trigger promotion check

**Infrastructure Layer:**
- [ ] `WaitlistRepository`
- [ ] `POST /api/v1/sessions/{id}/waitlist` - join
- [ ] `DELETE /api/v1/sessions/{id}/waitlist` - leave
- [ ] `GET /api/v1/sessions/{id}/waitlist` - view (admin/trainer only)

**Note:** Promotion logic is in domain service, NOT triggered by Django signals. The Application Layer handler calls the service and decides whether to save results.

---

## Milestone 4: Membership & Credits

### Issue: Credit Purchase (Vertical Slice)
**Priority:** P2 | **Estimate:** Medium

**Description:**
Users can purchase credit packages.

**Acceptance Criteria:**

**Domain Layer (`domain/membership/`):**
- [ ] `Credits` Value Object - validates non-negative
- [ ] `CreditPackage` Value Object (amount, price, validity_days)
- [ ] `Membership` Entity:
  ```python
  class Membership(AggregateRoot):
      def add_credits(self, package: CreditPackage) -> None:
          self.__credits = Credits(self.__credits.value + package.amount)
          self.__valid_until = max(
              self.__valid_until,
              datetime.utcnow() + timedelta(days=package.validity_days)
          )
          self._record(CreditsPurchasedEvent(...))

      def deduct_credits(self, amount: int, booking_id: str) -> None:
          if self.__credits.value < amount:
              raise InsufficientCreditsException()
          self.__credits = Credits(self.__credits.value - amount)
          self._record(CreditsDeductedEvent(...))
  ```

**Application Layer:**
- [ ] `PurchaseCreditsCommand` (user_id: str, package_id: str, payment_method_id: str)
- [ ] `PurchaseCreditsHandler` - orchestrates payment + credit addition

**Infrastructure Layer:**
- [ ] Stripe integration for payments
- [ ] `POST /api/v1/memberships/purchase`

---

### Issue: Credit Deduction on Booking
**Priority:** P2 | **Estimate:** Small

**Description:**
Automatically deduct credits when booking is confirmed.

**Acceptance Criteria:**
- [ ] Update `CreateBookingHandler` to deduct credits
- [ ] Update `CancelBookingHandler` to refund credits based on policy
- [ ] `CreditsDeductedEvent`, `CreditsRefundedEvent`
- [ ] Transaction must be atomic (booking + credit change)

---

## Milestone 5: Check-In System

### Issue: Session Check-In (Vertical Slice)
**Priority:** P2 | **Estimate:** Small

**Description:**
Trainers can check in attendees; late arrivals flagged.

**Acceptance Criteria:**

**Domain Layer:**
- [ ] `CheckIn` Entity:
  ```python
  class CheckIn(Entity):
      @classmethod
      def record(cls, booking: Booking, method: str, grace_period_minutes: int) -> "CheckIn":
          is_late = datetime.utcnow() > booking.starts_at + timedelta(minutes=grace_period_minutes)
          checkin = cls(booking_id=booking.id, method=method, is_late=is_late)
          return checkin
  ```
- [ ] `CheckInRecordedEvent`

**Application Layer:**
- [ ] `RecordCheckInCommand` (booking_id: str, method: str)
- [ ] `RecordCheckInHandler`

**Infrastructure Layer:**
- [ ] `POST /api/v1/bookings/{id}/checkin`
- [ ] QR code generation for bookings

---

## Milestone 6: Infrastructure & Events

### Issue: Event Bus Implementation
**Priority:** P1 | **Estimate:** Medium

**Description:**
Implement event bus following architecture patterns.

**Acceptance Criteria:**
- [ ] `EventBus` interface in application layer
- [ ] `InMemoryEventBus` for development/testing
- [ ] `RabbitMQEventBus` for production (optional)
- [ ] Events serialized as JSON (primitives only)
- [ ] Event handlers registered via DI container
- [ ] Event logging for debugging

**Pattern:**
```python
# Events created in Domain
booking = Booking.create(...)

# Events published in Application Layer (after commit)
with self.__unit_of_work() as uow:
    uow.bookings.save(booking)
    uow.commit()

self.__event_bus.publish(booking.pull_events())
```

---

### Issue: Celery Hold Expiry Worker
**Priority:** P2 | **Estimate:** Small

**Description:**
Background task to expire stale holds.

**Acceptance Criteria:**
- [ ] Celery beat task runs every minute
- [ ] Queries for holds past expiry time
- [ ] Publishes `HoldExpiredEvent` for each
- [ ] Updates hold status to expired
- [ ] Triggers waitlist promotion check

---

### Issue: Rate Limiting
**Priority:** P2 | **Estimate:** Small

**Description:**
Prevent abuse of hold creation.

**Acceptance Criteria:**
- [ ] Redis-based rate limiting
- [ ] Max 5 holds per user per minute
- [ ] Return 429 Too Many Requests when exceeded
- [ ] Configurable limits per endpoint

---

## Milestone 7: Angular Frontend

### Issue: Angular Auth Module
**Priority:** P1 | **Estimate:** Medium

**Acceptance Criteria:**
- [ ] Auth service with login/register/logout
- [ ] JWT token storage and refresh
- [ ] Route guards for protected routes
- [ ] HTTP interceptor for auth headers

---

### Issue: Angular Session Browser
**Priority:** P1 | **Estimate:** Medium

**Acceptance Criteria:**
- [ ] Session list with filtering (date, trainer, availability)
- [ ] Session cards showing availability
- [ ] Session detail view
- [ ] Responsive layout

---

### Issue: Angular Booking Flow
**Priority:** P1 | **Estimate:** Medium

**Acceptance Criteria:**
- [ ] Book button with capacity check
- [ ] Confirmation dialog
- [ ] Hold → Confirm flow (if hold system enabled)
- [ ] Toast notifications
- [ ] Error handling (409 full, etc.)

---

### Issue: Angular My Bookings
**Priority:** P1 | **Estimate:** Small

**Acceptance Criteria:**
- [ ] Tabbed view (Upcoming, Past, Cancelled)
- [ ] Cancel button with policy warning
- [ ] Booking cards with status badges

---

### Issue: Angular Waitlist UI
**Priority:** P2 | **Estimate:** Small

**Acceptance Criteria:**
- [ ] Join/Leave waitlist buttons
- [ ] Position display
- [ ] Promotion notification handling

---

### Issue: Angular Credits Display
**Priority:** P2 | **Estimate:** Small

**Acceptance Criteria:**
- [ ] Credits balance in header/dashboard
- [ ] Transaction history view
- [ ] Expiry warning display

---

## Architecture Checklist (Per Issue)

Use this checklist when implementing any issue:

- [ ] **Domain Layer**
  - [ ] Value Objects validate at creation
  - [ ] Entities have private attributes
  - [ ] Entities use expressive methods (not setters)
  - [ ] Events created inside domain (not handlers)
  - [ ] Events are self-contained (no back-filling queries)
  - [ ] Domain services are pure (return, don't save)

- [ ] **Application Layer**
  - [ ] Commands/Queries use JSON primitives only
  - [ ] Handlers use UnitOfWork for transactions
  - [ ] Events published AFTER transaction commit
  - [ ] No queries to build commands (atomic intent)

- [ ] **Infrastructure Layer**
  - [ ] Repositories for write-side only
  - [ ] Finders for read-side (return ViewModels)
  - [ ] Controllers map primitives ↔ domain objects

- [ ] **Error Handling**
  - [ ] Bare `raise` to preserve traceback
  - [ ] `raise X from e` when wrapping exceptions

---

## Issue Migration Guide

### Existing Issues to Close/Supersede

| Old Issue | Action | Replacement |
|-----------|--------|-------------|
| #1 Django Project Setup | **Update** | Project Structure + Layer Setup |
| #9 ClassTemplate Model | **Merge** | Class Template Management (Vertical Slice) |
| #10 ClassTemplate CRUD API | **Merge** | Class Template Management (Vertical Slice) |
| #12 ClassSession Model | **Merge** | Session Scheduling (Vertical Slice) |
| #13 Sessions List API | **Merge** | Session Scheduling (Vertical Slice) |
| #14 Session Detail | **Merge** | Session Scheduling (Vertical Slice) |
| #16 Booking Model | **Merge** | Create Booking with Capacity Check |
| #17 Capacity Validation | **Merge** | Create Booking with Capacity Check |
| #18 Cancel Booking | **Replace** | Cancel Booking with Refund Policy |
| #21 Waitlist Model | **Merge** | Waitlist with Auto-Promotion |
| #22 Waitlist Promotion | **Merge** | Waitlist with Auto-Promotion |
| #30 Redis + Spot Holds | **Replace** | Spot Hold System (Vertical Slice) |
| #34 Event-Driven Basics | **Replace** | Event Bus Implementation |

### Key Changes from Original Issues

1. **Vertical Slices** - Each issue delivers complete functionality (Domain → App → Infra)
2. **Rich Domain Models** - Behavior in entities, not anemic models
3. **CQRS Separation** - Repositories (write) vs Finders (read)
4. **Pure Domain Services** - No Django signals for business logic
5. **Self-Contained Events** - Full context, no back-filling queries
6. **JSON Primitives** - Commands/Queries/Events use only primitives
