CREATE ROLE ssscaner_app LOGIN PASSWORD 'ssscaner_secure_password';
CREATE ROLE ssscaner_readonly LOGIN PASSWORD 'ssscaner_readonly_password';

CREATE SCHEMA IF NOT EXISTS security;

CREATE TABLE IF NOT EXISTS security.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100),
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS security.failed_login_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address VARCHAR(64),
    email VARCHAR(255),
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user ON security.audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_failed_login_ip ON security.failed_login_attempts(ip_address);

ALTER TABLE security.audit_log OWNER TO ssscaner_app;
ALTER TABLE security.failed_login_attempts OWNER TO ssscaner_app;
GRANT USAGE ON SCHEMA security TO ssscaner_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA security TO ssscaner_app;
GRANT SELECT ON ALL TABLES IN SCHEMA security TO ssscaner_readonly;

CREATE OR REPLACE FUNCTION security.log_action() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO security.audit_log (user_id, action, table_name, record_id, details)
    VALUES (
        current_setting('request.user_id', true)::uuid,
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id::text, OLD.id::text),
        to_jsonb(COALESCE(NEW, OLD))
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE security.audit_log IS 'Registra cambios críticos y accesos de los usuarios al sistema.';
COMMENT ON TABLE security.failed_login_attempts IS 'Controla intentos de inicio de sesión fallidos para seguridad.';
