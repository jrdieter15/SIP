# SIPCall Database Schemas

## Database Design Overview

The SIPCall application uses PostgreSQL with the pgcrypto extension for encryption. The schema is designed for privacy, performance, and GDPR compliance.

## Core Tables

### 1. Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nextcloud_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    display_name VARCHAR(255),
    permissions JSONB DEFAULT '{"can_call": true, "is_admin": false}',
    privacy_consent BOOLEAN DEFAULT false,
    privacy_consent_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    last_login TIMESTAMPTZ
);

CREATE INDEX idx_users_nextcloud_id ON users(nextcloud_user_id);
CREATE INDEX idx_users_email ON users(email);
```

### 2. Calls Table
```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Encrypted sensitive data
    destination_number_enc BYTEA NOT NULL,
    caller_id_enc BYTEA,
    
    -- Call metadata
    call_uuid VARCHAR(255) UNIQUE, -- FreeSWITCH call UUID
    status VARCHAR(50) NOT NULL DEFAULT 'initiated',
    direction VARCHAR(20) NOT NULL DEFAULT 'outbound',
    
    -- Timing information
    initiated_at TIMESTAMPTZ DEFAULT now(),
    answered_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    
    -- Cost and billing
    cost_cents INTEGER,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Technical details
    codec VARCHAR(50),
    quality_score DECIMAL(3,2), -- 1.00 to 5.00
    disconnect_reason VARCHAR(100),
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_calls_user_id ON calls(user_id);
CREATE INDEX idx_calls_status ON calls(status);
CREATE INDEX idx_calls_initiated_at ON calls(initiated_at);
CREATE INDEX idx_calls_call_uuid ON calls(call_uuid);
```

### 3. Call Events Table
```sql
CREATE TABLE call_events (
    id SERIAL PRIMARY KEY,
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_call_events_call_id ON call_events(call_id);
CREATE INDEX idx_call_events_type ON call_events(event_type);
CREATE INDEX idx_call_events_timestamp ON call_events(timestamp);
```

### 4. System Configuration Table
```sql
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_system_config_key ON system_config(config_key);
```

### 5. Audit Logs Table
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
```

### 6. Rate Limiting Table
```sql
CREATE TABLE rate_limits (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMPTZ DEFAULT now(),
    window_duration_minutes INTEGER DEFAULT 60
);

CREATE INDEX idx_rate_limits_user_endpoint ON rate_limits(user_id, endpoint);
CREATE INDEX idx_rate_limits_window ON rate_limits(window_start);
```

## Encryption Functions

### Data Encryption/Decryption
```sql
-- Function to encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_data(data TEXT, key TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(data, key);
END;
$$ LANGUAGE plpgsql;

-- Function to decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_data(encrypted_data BYTEA, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(encrypted_data, key);
END;
$$ LANGUAGE plpgsql;
```

## Views for Analytics

### Call Statistics View
```sql
CREATE VIEW call_statistics AS
SELECT 
    DATE_TRUNC('day', initiated_at) as call_date,
    COUNT(*) as total_calls,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_calls,
    AVG(duration_seconds) as avg_duration,
    SUM(cost_cents) as total_cost_cents,
    AVG(quality_score) as avg_quality
FROM calls
GROUP BY DATE_TRUNC('day', initiated_at)
ORDER BY call_date DESC;
```

### User Activity View
```sql
CREATE VIEW user_activity AS
SELECT 
    u.id,
    u.display_name,
    COUNT(c.id) as total_calls,
    MAX(c.initiated_at) as last_call,
    SUM(c.cost_cents) as total_cost_cents,
    AVG(c.quality_score) as avg_quality
FROM users u
LEFT JOIN calls c ON u.id = c.user_id
GROUP BY u.id, u.display_name;
```

## Data Retention Policies

### Automatic Cleanup Functions
```sql
-- Function to clean up old call events (keep 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_call_events()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM call_events 
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old audit logs (keep 1 year)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs 
    WHERE timestamp < NOW() - INTERVAL '1 year';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
```

## GDPR Compliance Functions

### User Data Export
```sql
CREATE OR REPLACE FUNCTION export_user_data(target_user_id UUID, encryption_key TEXT)
RETURNS JSONB AS $$
DECLARE
    user_data JSONB;
    call_data JSONB;
BEGIN
    -- Get user information
    SELECT to_jsonb(u.*) INTO user_data
    FROM users u
    WHERE u.id = target_user_id;
    
    -- Get call history with decrypted data
    SELECT jsonb_agg(
        jsonb_build_object(
            'id', c.id,
            'destination_number', decrypt_data(c.destination_number_enc, encryption_key),
            'caller_id', decrypt_data(c.caller_id_enc, encryption_key),
            'status', c.status,
            'initiated_at', c.initiated_at,
            'duration_seconds', c.duration_seconds,
            'cost_cents', c.cost_cents
        )
    ) INTO call_data
    FROM calls c
    WHERE c.user_id = target_user_id;
    
    RETURN jsonb_build_object(
        'user', user_data,
        'calls', COALESCE(call_data, '[]'::jsonb)
    );
END;
$$ LANGUAGE plpgsql;
```

### User Data Deletion
```sql
CREATE OR REPLACE FUNCTION delete_user_data(target_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Delete call events first (foreign key constraint)
    DELETE FROM call_events 
    WHERE call_id IN (SELECT id FROM calls WHERE user_id = target_user_id);
    
    -- Delete calls
    DELETE FROM calls WHERE user_id = target_user_id;
    
    -- Delete rate limits
    DELETE FROM rate_limits WHERE user_id = target_user_id;
    
    -- Anonymize audit logs (don't delete for compliance)
    UPDATE audit_logs 
    SET user_id = NULL, details = jsonb_build_object('anonymized', true)
    WHERE user_id = target_user_id;
    
    -- Delete user record
    DELETE FROM users WHERE id = target_user_id;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;
```

## Performance Optimization

### Partitioning Strategy
```sql
-- Partition calls table by month for better performance
CREATE TABLE calls_y2025m01 PARTITION OF calls
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE calls_y2025m02 PARTITION OF calls
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Add more partitions as needed
```

### Materialized Views for Analytics
```sql
CREATE MATERIALIZED VIEW daily_call_summary AS
SELECT 
    DATE_TRUNC('day', initiated_at) as call_date,
    COUNT(*) as total_calls,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_calls,
    ROUND(AVG(duration_seconds)) as avg_duration,
    SUM(cost_cents) as total_cost_cents
FROM calls
GROUP BY DATE_TRUNC('day', initiated_at);

CREATE UNIQUE INDEX idx_daily_call_summary_date ON daily_call_summary(call_date);

-- Refresh materialized view daily
CREATE OR REPLACE FUNCTION refresh_daily_summary()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_call_summary;
END;
$$ LANGUAGE plpgsql;
```