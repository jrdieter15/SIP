# SIPCall API Documentation

## API Overview

The SIPCall API is built with FastAPI and provides RESTful endpoints for call management, authentication, and administration. All endpoints use JSON for request/response data and include proper HTTP status codes.

**Base URL:** `https://your-domain.com/api/v1`

## Authentication

All API endpoints (except `/auth`) require a valid JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

Tokens expire after 15 minutes and must be refreshed using the refresh endpoint.

## API Endpoints

### Authentication Endpoints

#### POST /auth
Authenticate user with Nextcloud OAuth2 code and receive JWT token.

**Request:**
```json
{
  "code": "oauth2_authorization_code",
  "redirect_uri": "https://your-nextcloud.com/apps/sipcall"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid authorization code
- `401` - Authentication failed

#### POST /auth/refresh
Refresh expired JWT token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Call Management Endpoints

#### POST /call
Initiate a new outbound call.

**Request:**
```json
{
  "destination_number": "+1234567890",
  "caller_id": "+0987654321",
  "privacy_mode": false
}
```

**Response:**
```json
{
  "call_id": "550e8400-e29b-41d4-a716-446655440000",
  "call_uuid": "freeswitch-uuid-12345",
  "status": "initiated",
  "destination_number": "+1234567890",
  "initiated_at": "2025-01-27T10:30:00Z"
}
```

**Status Codes:**
- `201` - Call initiated successfully
- `400` - Invalid phone number format
- `403` - User not authorized to make calls
- `429` - Rate limit exceeded
- `503` - FreeSWITCH unavailable

#### GET /call-status/{call_id}
Get current status of a specific call.

**Response:**
```json
{
  "call_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "duration_seconds": 45,
  "quality_score": 4.2,
  "last_updated": "2025-01-27T10:31:00Z"
}
```

**Call Status Values:**
- `initiated` - Call request received
- `ringing` - Destination is ringing
- `answered` - Call answered and in progress
- `completed` - Call ended normally
- `failed` - Call failed to connect
- `cancelled` - Call cancelled by user

#### POST /call/{call_id}/hangup
Terminate an active call.

**Response:**
```json
{
  "call_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "terminated",
  "final_duration": 120,
  "ended_at": "2025-01-27T10:32:00Z"
}
```

#### POST /call/{call_id}/hold
Put an active call on hold.

**Request:**
```json
{
  "hold": true
}
```

**Response:**
```json
{
  "call_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "on_hold",
  "hold_started": "2025-01-27T10:31:30Z"
}
```

#### POST /call/{call_id}/mute
Mute/unmute the microphone during a call.

**Request:**
```json
{
  "muted": true
}
```

**Response:**
```json
{
  "call_id": "550e8400-e29b-41d4-a716-446655440000",
  "muted": true,
  "updated_at": "2025-01-27T10:31:45Z"
}
```

### Call History Endpoints

#### GET /call-history
Retrieve user's call history with optional filtering.

**Query Parameters:**
- `from` (optional) - Start date (ISO 8601)
- `to` (optional) - End date (ISO 8601)
- `limit` (optional) - Number of records (default: 50, max: 100)
- `offset` (optional) - Pagination offset (default: 0)
- `status` (optional) - Filter by call status

**Response:**
```json
{
  "calls": [
    {
      "call_id": "550e8400-e29b-41d4-a716-446655440000",
      "destination_number": "+1234567890",
      "status": "completed",
      "initiated_at": "2025-01-27T10:30:00Z",
      "duration_seconds": 120,
      "cost_cents": 15,
      "quality_score": 4.2
    }
  ],
  "total_count": 1,
  "has_more": false
}
```

### User Management Endpoints

#### GET /user/profile
Get current user's profile information.

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "nextcloud_user_id": "john.doe",
  "display_name": "John Doe",
  "email": "john.doe@example.com",
  "permissions": {
    "can_call": true,
    "is_admin": false
  },
  "privacy_consent": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### PUT /user/profile
Update user profile information.

**Request:**
```json
{
  "display_name": "John Smith",
  "privacy_consent": true
}
```

### Privacy & GDPR Endpoints

#### GET /privacy/data-export
Export all user data for GDPR compliance.

**Response:**
```json
{
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "display_name": "John Doe",
    "email": "john.doe@example.com"
  },
  "calls": [
    {
      "destination_number": "+1234567890",
      "initiated_at": "2025-01-27T10:30:00Z",
      "duration_seconds": 120,
      "cost_cents": 15
    }
  ],
  "export_date": "2025-01-27T12:00:00Z"
}
```

#### POST /privacy/delete-account
Delete all user data (GDPR right to be forgotten).

**Response:**
```json
{
  "message": "User data deletion initiated",
  "deletion_id": "del_550e8400-e29b-41d4-a716-446655440000",
  "estimated_completion": "2025-01-27T13:00:00Z"
}
```

### Admin Endpoints

#### GET /admin/metrics
Get system metrics and analytics (admin only).

**Response:**
```json
{
  "system_health": {
    "freeswitch_status": "healthy",
    "database_status": "healthy",
    "active_calls": 5,
    "total_users": 150
  },
  "call_statistics": {
    "today": {
      "total_calls": 45,
      "completed_calls": 42,
      "failed_calls": 3,
      "total_duration_minutes": 1250
    },
    "this_month": {
      "total_calls": 1200,
      "total_cost_cents": 18500,
      "avg_quality_score": 4.3
    }
  }
}
```

#### GET /admin/users
Get list of all users (admin only).

**Query Parameters:**
- `limit` (optional) - Number of records (default: 50)
- `offset` (optional) - Pagination offset
- `search` (optional) - Search by name or email

**Response:**
```json
{
  "users": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "display_name": "John Doe",
      "email": "john.doe@example.com",
      "total_calls": 25,
      "last_call": "2025-01-27T10:30:00Z",
      "permissions": {
        "can_call": true,
        "is_admin": false
      }
    }
  ],
  "total_count": 150
}
```

#### PUT /admin/users/{user_id}/permissions
Update user permissions (admin only).

**Request:**
```json
{
  "can_call": true,
  "is_admin": false,
  "call_limit_per_day": 50
}
```

#### GET /admin/system-config
Get system configuration (admin only).

**Response:**
```json
{
  "sip_provider": {
    "name": "Telnyx",
    "status": "connected",
    "balance_cents": 50000
  },
  "rate_limits": {
    "calls_per_minute": 10,
    "calls_per_day": 100
  },
  "security": {
    "encryption_enabled": true,
    "audit_logging": true
  }
}
```

## WebSocket Endpoints

### /ws/call-events
Real-time call events via WebSocket connection.

**Connection:** `wss://your-domain.com/api/v1/ws/call-events?token=<jwt_token>`

**Event Types:**
```json
{
  "event_type": "call_status_changed",
  "call_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "answered",
  "timestamp": "2025-01-27T10:31:00Z"
}
```

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "INVALID_PHONE_NUMBER",
    "message": "The provided phone number is not valid",
    "details": {
      "field": "destination_number",
      "provided_value": "invalid-number"
    }
  },
  "timestamp": "2025-01-27T10:30:00Z",
  "request_id": "req_550e8400-e29b-41d4-a716-446655440000"
}
```

## Rate Limiting

API endpoints are rate limited per user:

- **Call endpoints:** 10 requests per minute
- **General endpoints:** 100 requests per minute
- **Admin endpoints:** 50 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1643284800
```

## API Versioning

The API uses URL versioning (`/api/v1/`). When breaking changes are introduced, a new version will be created (`/api/v2/`) with appropriate deprecation notices for older versions.

## SDK and Integration Examples

### JavaScript/TypeScript
```javascript
const sipCallAPI = new SIPCallAPI({
  baseURL: 'https://your-domain.com/api/v1',
  token: 'your-jwt-token'
});

// Make a call
const call = await sipCallAPI.initiateCall({
  destinationNumber: '+1234567890',
  privacyMode: false
});

// Monitor call status
const status = await sipCallAPI.getCallStatus(call.call_id);
```

### Python
```python
from sipcall_sdk import SIPCallClient

client = SIPCallClient(
    base_url='https://your-domain.com/api/v1',
    token='your-jwt-token'
)

# Make a call
call = client.initiate_call(
    destination_number='+1234567890',
    privacy_mode=False
)

# Get call history
history = client.get_call_history(limit=10)
```