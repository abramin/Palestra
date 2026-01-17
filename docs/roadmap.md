# Palestra Development Roadmap

This document outlines the recommended order for completing issues, organized by milestone and dependencies.

## Phase 1: Foundation (Milestone 1)

Start here - these establish the core patterns for the rest of the codebase.

| Issue | Title | Priority |
|-------|-------|----------|
| #5 | User Registration (Vertical Slice) | P0 |
| #6 | JWT Authentication | P0 |

## Phase 2: Scheduling (Milestone 2)

| Issue | Title | Priority |
|-------|-------|----------|
| #9 | Class Template Management | P1 |
| #12 | Session Scheduling | P1 |

## Phase 3: Core Booking (Milestone 3)

| Issue | Title | Priority |
|-------|-------|----------|
| #16 | Create Booking with Capacity Check | P1 |
| #18 | Cancel Booking with Refund Policy | P1 |
| #34 | Event Bus Implementation | P1 |

## Phase 4: Advanced Booking (Milestone 3 cont.)

| Issue | Title | Priority |
|-------|-------|----------|
| #30 | Spot Hold System | P2 |
| #21 | Waitlist with Auto-Promotion | P2 |
| #31 | Celery Hold Expiry Worker | P2 |

## Phase 5: Credits (Milestone 4)

| Issue | Title | Priority |
|-------|-------|----------|
| #24 | Credit Purchase | P2 |
| #25 | Credit Deduction on Booking | P2 |

## Phase 6: Check-In & Infrastructure (Milestones 5-6)

| Issue | Title | Priority |
|-------|-------|----------|
| #27 | Session Check-In | P2 |
| #33 | Rate Limiting | P2 |

## Phase 7: Angular Frontend (Milestone 7)

| Issue | Title | Priority |
|-------|-------|----------|
| #7 | Angular Auth Module | P1 |
| #15 | Angular Session Browser | P1 |
| #19 | Angular Booking Flow | P1 |
| #20 | Angular My Bookings | P1 |
| #23 | Angular Waitlist UI | P2 |
| #26 | Angular Credits Display | P2 |

## Key Dependencies

```
#5 User Registration
 └── #6 JWT Authentication
      └── #9 Class Template Management
           └── #12 Session Scheduling
                └── #16 Create Booking with Capacity Check
                     ├── #18 Cancel Booking with Refund Policy
                     ├── #30 Spot Hold System
                     │    └── #31 Celery Hold Expiry Worker
                     └── #21 Waitlist with Auto-Promotion

#24 Credit Purchase
 └── #25 Credit Deduction on Booking

#34 Event Bus Implementation (enables async events across all features)

Angular Frontend (can be developed in parallel after backend APIs exist)
 #7 Auth → #15 Session Browser → #19 Booking Flow → #20 My Bookings
```

## Priority Legend

- **P0**: Critical blockers - must complete first
- **P1**: High priority - core functionality
- **P2**: Medium priority - enhancements and advanced features
