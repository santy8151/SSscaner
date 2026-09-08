-- Generated review DDL; not a migration runner. No data or OEM specifications.

CREATE TABLE organizations (
	id VARCHAR(36) NOT NULL, 
	slug VARCHAR(80) NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (slug)
)

;


CREATE TABLE users (
	id VARCHAR(36) NOT NULL, 
	organization_id VARCHAR(36) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (organization_id, email), 
	UNIQUE (organization_id, id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)

;


CREATE TABLE vehicles (
	id VARCHAR(36) NOT NULL, 
	organization_id VARCHAR(36) NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	kind VARCHAR(30) NOT NULL, 
	manufacturer VARCHAR(100), 
	model VARCHAR(100), 
	year INTEGER, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (organization_id, id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)

;


CREATE TABLE audit_logs (
	id VARCHAR(36) NOT NULL, 
	organization_id VARCHAR(36) NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	action VARCHAR(80) NOT NULL, 
	resource_id VARCHAR(36) NOT NULL, 
	request_id VARCHAR(36) NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
)

;


CREATE TABLE auth_sessions (
	token_hash VARCHAR(64) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	expires_at FLOAT NOT NULL, 
	PRIMARY KEY (token_hash), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE device_profiles (
	id VARCHAR(36) NOT NULL, 
	organization_id VARCHAR(36) NOT NULL, 
	vehicle_id VARCHAR(36) NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	configuration JSON NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id, vehicle_id) REFERENCES vehicles (organization_id, id), 
	UNIQUE (organization_id, id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)

;


CREATE TABLE model_runs (
	id VARCHAR(36) NOT NULL, 
	organization_id VARCHAR(36) NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	configuration JSON NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	progress INTEGER NOT NULL, 
	result JSON, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
)

;


CREATE TABLE scan_sessions (
	id VARCHAR(36) NOT NULL, 
	organization_id VARCHAR(36) NOT NULL, 
	vehicle_id VARCHAR(36) NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	origin VARCHAR(20) NOT NULL, 
	protocol VARCHAR(20) NOT NULL, 
	scenario VARCHAR(40) NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id, vehicle_id) REFERENCES vehicles (organization_id, id), 
	FOREIGN KEY(organization_id, actor_id) REFERENCES users (organization_id, id), 
	UNIQUE (organization_id, id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)

;


CREATE TABLE device_readings (
	id VARCHAR(36) NOT NULL, 
	organization_id VARCHAR(36) NOT NULL, 
	profile_id VARCHAR(36) NOT NULL, 
	idempotency_key VARCHAR(100) NOT NULL, 
	payload JSON NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id, profile_id) REFERENCES device_profiles (organization_id, id), 
	UNIQUE (profile_id, idempotency_key), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)

;


CREATE TABLE telemetry_batches (
	id VARCHAR(36) NOT NULL, 
	organization_id VARCHAR(36) NOT NULL, 
	scan_id VARCHAR(36) NOT NULL, 
	idempotency_key VARCHAR(100) NOT NULL, 
	payload JSON NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id, scan_id) REFERENCES scan_sessions (organization_id, id), 
	UNIQUE (scan_id, idempotency_key), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)

;