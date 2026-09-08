CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'technician',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vehicles (
    id VARCHAR(64) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    make VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    year INT NOT NULL CHECK (year BETWEEN 1900 AND 2100),
    vehicle_type VARCHAR(50) DEFAULT 'car',
    vin VARCHAR(50) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS neural_nodes (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    algorithm VARCHAR(100) NOT NULL,
    is_trained BOOLEAN NOT NULL DEFAULT FALSE,
    accuracy NUMERIC(5,2) DEFAULT 0.00,
    epochs INT DEFAULT 50,
    parameters JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS diagnostic_results (
    id VARCHAR(64) PRIMARY KEY,
    vehicle_id VARCHAR(64) NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    node_id VARCHAR(64) NOT NULL REFERENCES neural_nodes(id),
    fault_detected BOOLEAN NOT NULL DEFAULT FALSE,
    fault_code VARCHAR(64),
    severity NUMERIC(5,2) DEFAULT 0.00,
    confidence NUMERIC(5,2) DEFAULT 0.00,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sensor_readings JSONB,
    recommendations JSONB,
    ai_explanation TEXT
);

CREATE TABLE IF NOT EXISTS scanner_logs (
    id VARCHAR(64) PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_type VARCHAR(50) NOT NULL,
    raw_data TEXT,
    interpreted_data JSONB,
    status VARCHAR(30) NOT NULL DEFAULT 'success'
);

CREATE TABLE IF NOT EXISTS measurements (
    id VARCHAR(64) PRIMARY KEY,
    vehicle_id VARCHAR(64) NOT NULL REFERENCES vehicles(id),
    user_id UUID NOT NULL REFERENCES users(id),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    measurement_type VARCHAR(50) NOT NULL,
    pressure_suction NUMERIC(8,2),
    pressure_discharge NUMERIC(8,2),
    temperature_evaporator NUMERIC(8,2),
    temperature_condenser NUMERIC(8,2),
    voltage NUMERIC(8,2),
    current NUMERIC(8,2),
    frequency_data JSONB,
    oscilloscope_data JSONB,
    raw_logs TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_vehicles_user_id ON vehicles(user_id);
CREATE INDEX IF NOT EXISTS idx_diag_vehicle_id ON diagnostic_results(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_log_device_id ON scanner_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_measurements_vehicle_id ON measurements(vehicle_id);

INSERT INTO users (id, email, password_hash, full_name, role) VALUES
    ('11111111-1111-1111-1111-111111111111', 'admin@ssscaner.local', crypt('admin123', gen_salt('bf')), 'Administrador', 'admin')
ON CONFLICT (email) DO NOTHING;

INSERT INTO neural_nodes (id, name, node_type, algorithm, is_trained, accuracy, epochs, parameters) VALUES
    ('compressor', 'Compresor', 'compressor', 'decision_tree', true, 94.20, 120, '{"threshold": 0.68}'),
    ('evaporator', 'Evaporador', 'evaporator', 'mlp_neural_network', true, 92.40, 150, '{"threshold": 0.64}'),
    ('condenser', 'Condensador', 'condenser', 'mlp_neural_network', true, 91.20, 170, '{"threshold": 0.66}'),
    ('chiller', 'Chiller', 'chiller', 'linear_regression', true, 89.40, 130, '{"threshold": 0.7}'),
    ('motor', 'Motor AC', 'ac_motor', 'bayesian_network', true, 93.60, 140, '{"threshold": 0.69}')
ON CONFLICT (id) DO NOTHING;
