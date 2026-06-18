-- AI Platform — Phase 1 schema
-- Run against the `aiplatform` database on Feynman.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- ROLES
-- ============================================================
CREATE TYPE user_role AS ENUM ('admin', 'professor', 'member');

CREATE TABLE roles (
    id          SERIAL PRIMARY KEY,
    name        user_role UNIQUE NOT NULL,
    description TEXT
);

INSERT INTO roles (name, description) VALUES
    ('admin',     'Full platform administrator'),
    ('professor', 'PI — audit access to all group projects'),
    ('member',    'Standard user: students, postdocs, staff');

-- ============================================================
-- USERS  (synced from LDAP on first login; role lives only here — never
-- overwritten from LDAP after initial creation)
-- ============================================================
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ldap_uid      VARCHAR(255) UNIQUE NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    display_name  VARCHAR(255) NOT NULL,
    role_id       INT NOT NULL REFERENCES roles(id),
    uid_number    INT,
    gid_number    INT,
    home_directory VARCHAR(255),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_users_ldap_uid ON users(ldap_uid);

-- ============================================================
-- CHATS
-- ============================================================
CREATE TABLE chats (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id       UUID NULL,                 -- FK added in Phase 2
    title            VARCHAR(255) NOT NULL DEFAULT 'New Chat',

    is_deleted       BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at       TIMESTAMPTZ,

    current_branch_id UUID,                      -- FK added after `branches` exists

    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chats_owner         ON chats(owner_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_chats_created_at    ON chats(created_at);
CREATE INDEX idx_chats_last_activity ON chats(last_activity_at) WHERE is_deleted = FALSE;

-- ============================================================
-- MESSAGES  (parent_message_id enables branching)
-- ============================================================
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');

CREATE TABLE messages (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id           UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    parent_message_id UUID NULL REFERENCES messages(id) ON DELETE SET NULL,
    role              message_role NOT NULL,
    content           TEXT NOT NULL,
    model_name        VARCHAR(100),
    input_tokens      INT,
    output_tokens     INT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_messages_chat   ON messages(chat_id, created_at);
CREATE INDEX idx_messages_parent ON messages(parent_message_id);

-- ============================================================
-- BRANCHES  (multiple saved branch tips per chat)
-- ============================================================
CREATE TABLE branches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id         UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    leaf_message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    label           VARCHAR(255) NOT NULL DEFAULT 'Branch',
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_branches_chat ON branches(chat_id);
CREATE UNIQUE INDEX idx_branches_one_default ON branches(chat_id) WHERE is_default = TRUE;

ALTER TABLE chats
    ADD CONSTRAINT fk_chats_current_branch
    FOREIGN KEY (current_branch_id) REFERENCES branches(id);

-- Bump chat aging fields whenever a new message is added
CREATE OR REPLACE FUNCTION update_chat_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chats
    SET last_activity_at = now(), updated_at = now()
    WHERE id = NEW.chat_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_messages_update_chat_activity
AFTER INSERT ON messages
FOR EACH ROW EXECUTE FUNCTION update_chat_activity();

-- ============================================================
-- CHAT ARCHIVES  (chat row is deleted from `chats` on archive; this is the
-- only remaining record, pointing at the exported JSON on CephFS)
-- ============================================================
CREATE TABLE chat_archives (
    id                         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_chat_id          UUID NOT NULL,        -- no FK; original row is gone
    owner_id                  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id                UUID NULL,
    title                     VARCHAR(255) NOT NULL,
    archive_path              TEXT NOT NULL,         -- CephFS path to exported JSON (gzip)
    message_count             INT NOT NULL,
    original_created_at       TIMESTAMPTZ NOT NULL,
    original_last_activity_at TIMESTAMPTZ NOT NULL,
    archived_by               UUID NOT NULL REFERENCES users(id),
    archived_at                TIMESTAMPTZ NOT NULL DEFAULT now(),

    restored_at                TIMESTAMPTZ,
    restored_to_chat_id        UUID,
    restored_by                 UUID REFERENCES users(id)
);

CREATE INDEX idx_chat_archives_owner       ON chat_archives(owner_id);
CREATE INDEX idx_chat_archives_archived_at ON chat_archives(archived_at);

-- ============================================================
-- AUDIT LOG
-- ============================================================
CREATE TABLE audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id    UUID REFERENCES users(id),     -- NULL = system/automated action
    action      VARCHAR(100) NOT NULL,         -- 'chat_export', 'role_change', 'status_change', ...
    target_type VARCHAR(50) NOT NULL,          -- 'chat', 'user', 'project', etc.
    target_id   UUID,
    metadata    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_log_actor   ON audit_log(actor_id);
CREATE INDEX idx_audit_log_action  ON audit_log(action);
CREATE INDEX idx_audit_log_target  ON audit_log(target_type, target_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);

-- ============================================================
-- CONNECTORS  (per-user external API endpoints; API keys encrypted at the
-- application layer with Fernet before being written to api_key_encrypted)
-- ============================================================
CREATE TABLE connectors (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider           VARCHAR(50) NOT NULL,            -- 'openai', 'anthropic', 'google_gemini', 'openrouter', 'custom'
    label              VARCHAR(255) NOT NULL,
    base_url           TEXT NOT NULL,
    api_key_encrypted  BYTEA,                           -- NULL until user configures it
    is_seeded          BOOLEAN NOT NULL DEFAULT FALSE,   -- TRUE for the 4 defaults; locked + non-deletable
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_connectors_user ON connectors(user_id);
CREATE UNIQUE INDEX idx_connectors_user_provider_seeded
    ON connectors(user_id, provider) WHERE is_seeded = TRUE;
