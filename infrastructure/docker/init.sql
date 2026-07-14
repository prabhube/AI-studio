-- ============================================================
-- Prabhu AI Studio — PostgreSQL Initialization Script
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for full-text search support
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable pgcrypto for additional hashing utilities
CREATE EXTENSION IF NOT EXISTS pgcrypto;
