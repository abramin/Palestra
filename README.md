# Palestra (FitFlow)

A booking and client management platform for personal trainers and fitness studios.

## Documentation

- **[Product Requirements (PRD)](docs/prd.md)** - Full product vision, features, and technical requirements
- **[Architecture Guide (CLAUDE.md)](CLAUDE.md)** - Development rules, architectural guardrails, and coding standards

## Architecture

This project follows **Domain-Driven Design (DDD)** with **CQRS** and **Event-Driven Architecture**.

```
src/
├── domain/           # Business logic, entities, value objects, domain events
├── application/      # Command/Query handlers, orchestration
├── infrastructure/   # External integrations, persistence, controllers
└── shared/           # Cross-cutting concerns
```

## Tech Stack

- **Backend**: Python/Django REST framework
- **Database**: PostgreSQL
- **Cache**: Redis
- **Message Broker**: Kafka/RabbitMQ
- **Async Workers**: Celery
- **Infrastructure**: Docker, Kubernetes, AWS