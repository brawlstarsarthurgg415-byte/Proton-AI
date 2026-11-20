-- Proton Authority schema v2. Additive migration; existing data is preserved.
CREATE TABLE IF NOT EXISTS authority_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(40) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(24) NOT NULL DEFAULT 'user'
        CHECK (role IN ('user', 'official_admin', 'ceo')),
    totp_secret TEXT,
    totp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (totp_enabled = FALSE OR totp_secret IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS authority_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES authority_users(id) ON DELETE CASCADE,
    token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS authority_sessions_user_idx ON authority_sessions(user_id, expires_at DESC);
CREATE TABLE IF NOT EXISTS authority_ai_profiles (
    user_id UUID PRIMARY KEY REFERENCES authority_users(id) ON DELETE CASCADE,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS authority_ai_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES authority_users(id) ON DELETE CASCADE,
    content TEXT NOT NULL CHECK (char_length(content) BETWEEN 1 AND 10000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS authority_ai_memories_user_idx ON authority_ai_memories(user_id, created_at DESC);
