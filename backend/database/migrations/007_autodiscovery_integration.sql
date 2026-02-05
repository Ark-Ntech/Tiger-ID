-- Migration 007: Auto-discovery Integration Fields
--
-- Adds source tracking columns to investigations and verification_queue tables
-- to support the auto-discovery pipeline integration.
--
-- New fields:
--   investigations:
--     - source: "user_upload" or "auto_discovery"
--     - source_tiger_id: Tiger ID that triggered auto-investigation
--     - source_image_id: Image ID that triggered auto-investigation
--
--   verification_queue:
--     - source: "auto_discovery" or "user_upload"
--     - investigation_id: Source investigation reference
--
-- This migration is idempotent and safe to run multiple times.
-- SQLite does not support IF NOT EXISTS for ADD COLUMN, so we use
-- a pattern that ignores "duplicate column name" errors.

-- ============================================================================
-- INVESTIGATIONS TABLE
-- ============================================================================

-- Add source column to investigations
-- Default: "user_upload" for backward compatibility
ALTER TABLE investigations ADD COLUMN source VARCHAR(50) DEFAULT 'user_upload';

-- Add source_tiger_id column to investigations
ALTER TABLE investigations ADD COLUMN source_tiger_id VARCHAR(36);

-- Add source_image_id column to investigations
ALTER TABLE investigations ADD COLUMN source_image_id VARCHAR(36);

-- ============================================================================
-- VERIFICATION_QUEUE TABLE
-- ============================================================================

-- Add source column to verification_queue
ALTER TABLE verification_queue ADD COLUMN source VARCHAR(50);

-- Add investigation_id column to verification_queue
ALTER TABLE verification_queue ADD COLUMN investigation_id VARCHAR(36) REFERENCES investigations(investigation_id);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index on investigations.source for filtering by source type
CREATE INDEX IF NOT EXISTS idx_investigations_source ON investigations(source);

-- Index on investigations.source_tiger_id for finding investigations by trigger tiger
CREATE INDEX IF NOT EXISTS idx_investigations_source_tiger_id ON investigations(source_tiger_id);

-- Index on investigations.source_image_id for finding investigations by trigger image
CREATE INDEX IF NOT EXISTS idx_investigations_source_image_id ON investigations(source_image_id);

-- Index on verification_queue.source for filtering
CREATE INDEX IF NOT EXISTS idx_verification_queue_source ON verification_queue(source);

-- Index on verification_queue.investigation_id for joining
CREATE INDEX IF NOT EXISTS idx_verification_queue_investigation_id ON verification_queue(investigation_id);

-- ============================================================================
-- MIGRATION METADATA
-- ============================================================================

-- Record migration completion (optional tracking table)
-- This is a no-op if the table doesn't exist
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
SELECT '007_autodiscovery_integration', CURRENT_TIMESTAMP
WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations');
