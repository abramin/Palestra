Architectural Guardrails & Ruleset

1. Layered Responsibilities
   Domain Layer: Must contain all business logic, invariants, and validations. Entities and Value Objects must be "rich" (encapsulate behavior).

Application Layer: Thin orchestrators (Command/Query Handlers). Responsible for:

Managing transactions via UnitOfWork.

Side effects: Calling repository.save() and event_bus.publish().

Mapping between primitives and domain objects.

Infrastructure Layer: External integrations (Stripe, etc.) and entry points (Controllers). Integration models here should mirror the external provider's API exactly.

2. Code Design Rules
   Rich Models: Attributes must be private. Use expressive methods (e.g., order.cancel()) instead of setters.

Value Objects: Use them for data that requires validation at creation (e.g., Email, Price).

No Message Chains: Avoid ORM lazy-loading (e.g., user.tickets). Always fetch related entities via their own repository: ticket_repository.find_by_user_id(user.id).

JSON Primitives: All Commands, Queries, and Events must use only str, int, float, bool, list, dict, or None. Convert UUID and datetime to strings at the boundary.

3. Transactionality & Side Effects
   Transaction Boundary: Must be in the Application Layer (Command Handler) using with self.\_\_unit_of_work():.

Pure Domain Services: Domain services must not save to repositories or publish events. They must return entities/events to the handler.

Atomic Logic: Never execute a Query to decide how to build a Command. Commands must be self-contained units of intent.

4. CQRS (Command Query Responsibility Segregation)
   Repositories: Use only for the write-side (fetching entities to modify them).

Finders: Use for the read-side (fetching data for display/API).

Must follow SRP (one class, one public find() method).

Must handle pagination and filtering.

Must return ViewModels (QueryResponses), not domain entities.

5. Event-Driven Patterns
   Instantiation: Create events inside the Domain (Entities or Domain Services), never in the Application Layer.

Aggregate Roots: If using them, use record(event) and pull_events() to manage events internally.

Context: Events must be self-contained (carry name, email, etc.), not just an id, to prevent "back-filling" queries by consumers.

Requested Suffix: Use ...RequestedEvent for async side effects that act as a bridge to future async commands.

6. Error Handling
   Preserve Tracebacks: Never use raise e. Use a bare raise to re-propagate.

Exception Mapping: When wrapping errors, use raise CustomException() from e.

7. Data Consistency
   Foreign Keys: Avoid DB-level FKs on command-side replicas (replicated data from other services) to handle eventual consistency without failing consumers.
