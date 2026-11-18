-- Proton-AI PostgreSQL schema v1
-- Safe to run repeatedly. No existing tables or rows are dropped.

CREATE TABLE IF NOT EXISTS knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL CHECK (char_length(content) BETWEEN 1 AND 20000),
    kind VARCHAR(32) NOT NULL DEFAULT 'lesson'
        CHECK (kind IN ('lesson', 'correction', 'reference', 'ownership_claim')),
    source_label TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'pending_review'
        CHECK (status IN ('pending_review', 'quarantined', 'approved', 'rejected', 'declaration_unverified')),
    guardian_verdict VARCHAR(24)
        CHECK (guardian_verdict IS NULL OR guardian_verdict IN ('safe', 'unsafe', 'controversial', 'unknown')),
    guardian_model TEXT,
    guardian_confidence REAL CHECK (guardian_confidence IS NULL OR guardian_confidence BETWEEN 0 AND 1),
    training_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    content_hash CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    CONSTRAINT knowledge_training_gate CHECK (
        training_eligible = FALSE OR (status = 'approved' AND kind IN ('lesson', 'correction', 'reference'))
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS knowledge_content_hash_uq ON knowledge(content_hash);
CREATE INDEX IF NOT EXISTS knowledge_status_created_idx ON knowledge(status, created_at DESC);
CREATE INDEX IF NOT EXISTS knowledge_training_idx ON knowledge(training_eligible) WHERE training_eligible = TRUE;

CREATE TABLE IF NOT EXISTS knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_id UUID NOT NULL REFERENCES knowledge(id) ON DELETE CASCADE,
    url TEXT NOT NULL CHECK (url ~ '^https?://'),
    title TEXT,
    retrieved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (knowledge_id, url)
);
CREATE INDEX IF NOT EXISTS knowledge_sources_knowledge_idx ON knowledge_sources(knowledge_id);

CREATE TABLE IF NOT EXISTS guardian_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_id UUID NOT NULL REFERENCES knowledge(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    verdict VARCHAR(24) NOT NULL
        CHECK (verdict IN ('safe', 'unsafe', 'controversial', 'unknown')),
    categories JSONB NOT NULL DEFAULT '[]'::jsonb,
    rationale TEXT,
    confidence REAL CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    action VARCHAR(24) NOT NULL DEFAULT 'quarantine'
        CHECK (action IN ('quarantine', 'manual_review', 'reject')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS guardian_reviews_knowledge_idx ON guardian_reviews(knowledge_id, created_at DESC);

CREATE TABLE IF NOT EXISTS training_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,
    dataset_version TEXT,
    status VARCHAR(24) NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
    examples_count INTEGER NOT NULL DEFAULT 0 CHECK (examples_count >= 0),
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    artifact_uri TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(40) NOT NULL,
    entity_id UUID,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(120) NOT NULL DEFAULT 'system',
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS audit_events_entity_idx ON audit_events(entity_type, entity_id, created_at DESC);
CREATE INDEX IF NOT EXISTS audit_events_created_idx ON audit_events(created_at DESC);

INSERT INTO audit_events(entity_type, event_type, actor, details)
SELECT 'system', 'schema_initialized', 'proton-migration', '{"schema_version":1}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM audit_events
    WHERE entity_type = 'system' AND event_type = 'schema_initialized'
      AND details->>'schema_version' = '1'
);
