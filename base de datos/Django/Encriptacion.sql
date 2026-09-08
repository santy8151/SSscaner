CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS app_encryption_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL UNIQUE,
    key_value BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS encrypted_session_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_encrypted_session_user ON encrypted_session_data(user_id);
CREATE INDEX IF NOT EXISTS idx_encrypted_session_expiry ON encrypted_session_data(expires_at);

INSERT INTO app_encryption_keys (key_name, key_value)
VALUES (
    'ssscaner_default_key',
    gen_random_bytes(32)
)
ON CONFLICT (key_name) DO NOTHING;

COMMENT ON TABLE app_encryption_keys IS 'Almacena las claves de cifrado para tokens y sesiones.';
COMMENT ON TABLE encrypted_session_data IS 'Guarda información de sesión cifrada en la capa de persistencia Django.';
