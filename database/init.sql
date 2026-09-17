-- NumberGuard Database Initialization Script
-- Initializes extensions and security parameters

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone to UTC
SET timezone TO 'UTC';
