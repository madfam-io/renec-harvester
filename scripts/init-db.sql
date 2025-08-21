-- Initialize RENEC Harvester database
-- This script creates the basic database structure

-- Set timezone
SET timezone = 'America/Mexico_City';

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create basic schema (Alembic will handle full migrations)
CREATE SCHEMA IF NOT EXISTS public;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE renec_harvester TO renec;
GRANT ALL ON SCHEMA public TO renec;

-- Log initialization
INSERT INTO pg_stat_statements_info VALUES ('RENEC Database initialized') ON CONFLICT DO NOTHING;