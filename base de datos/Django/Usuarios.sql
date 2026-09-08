CREATE TABLE IF NOT EXISTS auth_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(150) DEFAULT '',
    last_name VARCHAR(150) DEFAULT '',
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    date_joined TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS user_profile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    vehicle_brand VARCHAR(100),
    vehicle_model VARCHAR(100),
    workshop_name VARCHAR(150),
    phone VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO auth_user (id, username, email, password, first_name, last_name, is_staff, is_superuser)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'admin',
    'admin@ssscaner.local',
    'pbkdf2_sha256$260000$example$replace_with_django_hash',
    'Administrador',
    'SSSCANER',
    TRUE,
    TRUE
)
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_profile (user_id, vehicle_brand, vehicle_model, workshop_name)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'Generic',
    'SSSCANER',
    'Taller de diagnóstico local'
)
ON CONFLICT (user_id) DO NOTHING;
