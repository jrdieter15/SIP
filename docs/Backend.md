# SIPCall Backend Documentation

## Architecture Overview

The SIPCall backend is built using FastAPI (Python) and serves as the bridge between the Nextcloud frontend and the FreeSWITCH telephony server. It handles authentication, call management, logging, and integration with SIP trunk providers.

## Technology Stack

- **Framework:** FastAPI 0.104+
- **Database:** PostgreSQL 16 with pgcrypto extension
- **Authentication:** JWT tokens with Nextcloud OAuth2 integration
- **Telephony:** FreeSWITCH Event Socket Library (ESL)
- **Caching/Rate Limiting:** Redis
- **Deployment:** Docker containers

## Core Components

### 1. Application Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection and models
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py   # JWT token management
│   │   └── dependencies.py  # Auth dependencies
│   ├── api/
│   │   ├── __init__.py
│   │   ├── calls.py         # Call management endpoints
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── admin.py         # Admin dashboard endpoints
│   │   └── privacy.py       # GDPR compliance endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── freeswitch.py    # FreeSWITCH ESL integration
│   │   ├── sip_provider.py  # SIP trunk provider integration
│   │   └── encryption.py    # Data encryption services
│   └── models/
│       ├── __init__.py
│       ├── call.py          # Call data models
│       ├── user.py          # User data models
│       └── admin.py         # Admin data models
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### 2. Database Operations

#### Connection Management
- SQLModel for ORM operations
- Connection pooling for performance
- Automatic retry logic for failed connections
- Health checks for database availability

#### Encryption Strategy
- Use PostgreSQL pgcrypto extension
- Encrypt sensitive fields (phone numbers, call metadata)
- Key rotation strategy for long-term security
- Secure key storage in environment variables

### 3. FreeSWITCH Integration

#### Event Socket Library (ESL)
- Real-time connection to FreeSWITCH
- Call origination and termination
- Call status monitoring
- Event handling for call state changes

#### Call Flow Management
1. Receive call request from frontend
2. Validate user permissions and rate limits
3. Originate call via FreeSWITCH ESL
4. Monitor call progress and status
5. Log call details to database
6. Return call status to frontend

### 4. Authentication & Security

#### JWT Implementation
- Token-based authentication
- 15-minute token expiry with refresh mechanism
- Secure token storage and validation
- Integration with Nextcloud OAuth2

#### Rate Limiting
- Redis-based rate limiting
- Per-user call limits
- API endpoint protection
- Abuse prevention mechanisms

### 5. API Endpoints

#### Core Endpoints
- `POST /auth` - Authenticate with Nextcloud OAuth
- `POST /call` - Initiate new call
- `GET /call-status/{uuid}` - Get call status
- `GET /call-history` - Retrieve call history
- `POST /privacy/delete` - GDPR data deletion

#### Admin Endpoints
- `GET /admin/metrics` - System metrics and analytics
- `GET /admin/users` - User management
- `POST /admin/config` - System configuration

### 6. Error Handling

#### Exception Management
- Custom exception classes for different error types
- Structured error responses with proper HTTP status codes
- Logging of all errors for debugging
- User-friendly error messages

#### Retry Logic
- Automatic retry for transient failures
- Exponential backoff for FreeSWITCH connections
- Circuit breaker pattern for external services
- Graceful degradation when services are unavailable

### 7. Monitoring & Logging

#### Application Logging
- Structured logging with JSON format
- Different log levels (DEBUG, INFO, WARNING, ERROR)
- Request/response logging for API calls
- Performance metrics logging

#### Health Checks
- Database connectivity checks
- FreeSWITCH connection status
- SIP trunk provider availability
- Redis cache connectivity

### 8. Configuration Management

#### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/sipcall
DATABASE_ENCRYPTION_KEY=your-encryption-key

# FreeSWITCH
FREESWITCH_HOST=localhost
FREESWITCH_PORT=8021
FREESWITCH_PASSWORD=your-password

# Authentication
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=15

# SIP Provider
SIP_PROVIDER_API_KEY=your-provider-key
SIP_PROVIDER_BASE_URL=https://api.telnyx.com

# Redis
REDIS_URL=redis://localhost:6379

# Security
CORS_ORIGINS=["http://localhost:3000"]
RATE_LIMIT_CALLS_PER_MINUTE=10
```

### 9. Performance Considerations

#### Optimization Strategies
- Database query optimization with proper indexing
- Connection pooling for database and Redis
- Async/await for I/O operations
- Caching of frequently accessed data

#### Scalability Planning
- Horizontal scaling with load balancers
- Database read replicas for analytics
- Redis clustering for high availability
- Microservice architecture for future expansion

### 10. Security Best Practices

#### Data Protection
- Encryption of sensitive data at rest
- TLS for all communications
- Input validation and sanitization
- SQL injection prevention

#### Access Control
- Role-based access control (RBAC)
- API key management
- Audit logging for all operations
- Regular security updates and patches