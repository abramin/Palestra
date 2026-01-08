# PRD: FitFlow - PT Session & Class Booking Platform

## Product Vision

A booking and client management platform for personal trainers and fitness studios that handles high-volume session scheduling, capacity management, payment processing, and client relationship tracking at scale.

## Problem Statement

Personal trainers managing 50-200+ active clients face operational chaos: double-bookings, manual payment tracking, no-shows without accountability, waitlist management via spreadsheet, and inability to analyze client patterns. As practice scales, manual processes break down.

Studios running group classes need real-time capacity enforcement, hold mechanisms to prevent overbooking, automated waitlist promotion, and operational dashboards for coaches and admins.

## User Personas

**Trainer (Alex)**: Runs 1:1 sessions and small group classes. Needs schedule visibility, client history, program tracking, payment status, and no-show patterns.

**Client (Member)**: Books sessions/classes, manages credit packages, tracks attendance history, receives reminders, joins waitlists.

**Studio Admin**: Manages multiple trainers, monitors capacity across all sessions, handles billing disputes, analyzes utilization and revenue.

## Core Features

### 1. Session & Class Management

**Class Templates**: Define recurring class types (e.g., "Morning Strength" - 60min, max 12 people, trainer: Alex). Templates spawn actual sessions.

**Session Creation**: Admins/trainers create specific sessions from templates (date, time, capacity override, trainer assignment). Sessions have states: draft, published, in-progress, completed, cancelled.

**Capacity Enforcement**: Hard limit preventing `confirmed_bookings + active_holds > capacity`. Enforced at database level with row locking.

**1:1 Sessions**: Trainer defines availability blocks. Clients book specific slots. Capacity = 1.

### 2. Booking Flow

**Browse & Filter**: Clients view upcoming sessions filtered by date, trainer, class type, available spots.

**Spot Hold**: Client requests a spot. System creates 10-minute hold, decrementing available capacity. Hold expires automatically if not confirmed.

**Confirmation**: Client confirms within hold window. Hold converts to booking, payment processed (or credit deducted).

**Waitlist**: If session full, client joins waitlist. When spot opens (cancellation, no-show), first waitlist member gets notification and 5-minute priority hold.

**Cancellation Policy**: 
- >24h before: full credit refund
- 12-24h: 50% credit forfeiture  
- <12h: full credit forfeiture
- No-show: full credit loss + flag for pattern analysis

### 3. Payment & Credit System

**Membership Plans**: Monthly/annual unlimited or credit-based packages (e.g., "10 sessions for $500").

**Credit Ledger**: Track credit purchases, usage, expiry. Credits have validity periods (e.g., 3 months).

**Payment Processing**: Stripe integration for purchases. Support for refunds, disputes.

**Pricing Tiers**: Peak vs off-peak pricing. Member vs drop-in rates.

### 4. Client Management

**Client Profile**: Contact info, membership status, credits balance, attendance history, program assignments, notes.

**Program Tracking**: Trainer assigns workout programs. Track exercises, sets, reps, progression over time.

**Attendance Analytics**: Client-level: attendance rate, favorite classes, no-show pattern. Aggregate: utilization by time slot, revenue per session type.

**Communication**: Automated reminders (24h before, 1h before), waitlist notifications, credit expiry warnings.

### 5. Check-In System

**QR Code**: Client receives QR code with booking confirmation. Trainer/kiosk scans at session start.

**Manual Check-In**: Trainer checks attendance list, marks present/absent.

**Late Check-In**: Configurable grace period (e.g., 10 minutes). After that, marked as no-show.

### 6. Operational Dashboard

**Trainer View**: Today's schedule, upcoming week, client attendance status, recent no-shows, earnings summary.

**Admin View**: Live capacity across all sessions, waitlist lengths, revenue dashboard, trainer utilization, client churn indicators.

**Incident Tracking**: Log equipment issues, client incidents, session notes.

## Technical Requirements

### Stack Alignment with Fever

**Backend**: Python/Django REST framework  
**Database**: PostgreSQL (bookings, users, sessions, ledger)  
**Cache**: Redis (schedule cache, hold TTLs, rate limiting)  
**Message Broker**: Kafka or RabbitMQ  
**Async Workers**: Celery  
**Frontend**: Angular (admin/trainer dashboard), mobile-responsive member UI  
**Infrastructure**: Docker, Kubernetes, AWS (RDS, ElastiCache, MSK/MQ, S3, CloudWatch)

### Domain Model (Postgres)

```
users (id, email, role, created_at)
memberships (id, user_id, plan_type, credits_balance, valid_until)
credit_transactions (id, user_id, amount, type, booking_id, created_at)

class_templates (id, name, duration, default_capacity, trainer_id)
class_sessions (id, template_id, trainer_id, starts_at, ends_at, capacity, status)

spot_holds (id, session_id, user_id, expires_at, status, created_at)
bookings (id, session_id, user_id, status, credits_used, created_at)
waitlist_entries (id, session_id, user_id, position, created_at)

checkins (id, booking_id, method, checked_in_at, late)
programs (id, trainer_id, client_id, name, start_date, end_date)
program_sessions (id, program_id, session_date, exercises_json)

audit_log (id, entity_type, entity_id, action, user_id, timestamp, details)
```

### Redis Cache Strategy

**Keys**:
- `session:{id}:holds` (sorted set, score = expiry timestamp)
- `session:{id}:booked_count` (counter)
- `schedule:date:{YYYY-MM-DD}` (cached session list)
- `user:{id}:rate_limit:hold` (rate limit hold creation)

**TTL**: Hold keys expire with hold timeout. Schedule cache: 5 minutes.

### Event-Driven Architecture (Kafka/RabbitMQ)

**Topics/Queues**:
- `hold.created`, `hold.expired`, `hold.confirmed`
- `booking.confirmed`, `booking.cancelled`, `booking.noshow`
- `checkin.recorded`
- `waitlist.joined`, `waitlist.promoted`
- `payment.processed`, `payment.failed`
- `credit.purchased`, `credit.used`, `credit.expiring`

**Consumers**:
- **Notifications Service**: Email/SMS/push for booking confirmations, reminders, waitlist promotions
- **Analytics Service**: Aggregate metrics, update dashboards
- **Policy Enforcer**: Handle cancellation refunds, no-show penalties, credit expiry
- **Waitlist Manager**: Promote next person when spot opens

### API Design (RESTful)

```
GET    /sessions?from=<date>&to=<date>&trainer_id=<id>&type=<type>
GET    /sessions/{id}
POST   /sessions/{id}/hold
POST   /holds/{id}/confirm
DELETE /holds/{id}

GET    /bookings/me
POST   /bookings/{id}/cancel
POST   /bookings/{id}/checkin

GET    /waitlist/{session_id}
POST   /waitlist/{session_id}/join
DELETE /waitlist/{session_id}

GET    /clients/{id}/profile
GET    /clients/{id}/attendance
POST   /clients/{id}/programs

GET    /memberships/me
POST   /memberships/purchase
GET    /credits/transactions

POST   /admin/sessions (create session)
PATCH  /admin/sessions/{id} (update capacity, cancel)
GET    /admin/dashboard (live stats)
```

### Scalability & Reliability

**Capacity Enforcement**: Postgres row-level locking on `class_sessions` during hold/booking creation. Transaction isolation level: SERIALIZABLE for critical paths.

**Hold Expiry**: Celery beat task runs every minute, queries Redis for expired holds, publishes `hold.expired` events. Consumer rolls back capacity, notifies waitlist.

**Rate Limiting**: Redis-based rate limiting on hold creation (e.g., max 5 holds per user per minute) to prevent abuse.

**Idempotency**: All state-changing endpoints require idempotency keys. Duplicate requests within 24h return cached response.

**Observability**: ELK stack for logging, Prometheus + Grafana for metrics (hold latency, booking success rate, capacity utilization), distributed tracing with Jaeger.

**High Availability**: K8s deployment with HPA on API and worker pods. RDS Multi-AZ, ElastiCache cluster mode.

## Success Metrics

**Operational**:
- Hold-to-booking conversion rate >70%
- Hold expiry rate <20%
- Average hold response time <200ms
- Waitlist promotion success rate >60% (promoted member confirms)

**Business**:
- Session utilization rate >80%
- No-show rate <10%
- Credit expiry rate <5% (indicator of engagement)
- Client retention rate >85% (3-month window)

**Technical**:
- API p95 latency <500ms
- Capacity enforcement: 0 overbookings
- Event processing lag <5 seconds
- System uptime >99.5%

## Out of Scope (V1)

- Multi-location/franchise management
- Video streaming for remote sessions
- In-app messaging between trainer/client
- Nutrition tracking integration
- Social features (friend invites, leaderboards)
- Third-party calendar sync (Google Calendar, iCal)

## Future Considerations (V2+)

- Dynamic pricing based on demand
- AI-powered schedule optimization for trainers
- Client progression predictions (ML on attendance/performance data)
- Marketplace for trainers (clients discover and book across multiple trainers)
- Corporate/group booking accounts
