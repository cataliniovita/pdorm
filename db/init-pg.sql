\connect demo

-- Clean slate (drop in dependency order)
DROP VIEW IF EXISTS v_users_emails;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS fruit;
DROP TABLE IF EXISTS users;

-- Users table
CREATE TABLE users (
  id   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'user'
);

INSERT INTO users (name, email, role) VALUES
('alice', 'alice@example.com', 'admin'),
('bob', 'bob@example.com', 'user'),
('charlie', 'charlie@example.com', 'user');

-- Fruit table
CREATE TABLE fruit (
  id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name  VARCHAR(50) NOT NULL,
  color VARCHAR(50) NOT NULL,
  price NUMERIC(10,2) NOT NULL DEFAULT 0.00
);

INSERT INTO fruit (name, color, price) VALUES
('apple', 'red', 1.20),
('banana', 'yellow', 0.80),
('pear', 'green', 1.10);

-- Products table
CREATE TABLE products (
  id   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sku  VARCHAR(64) NOT NULL,
  title VARCHAR(255) NOT NULL,
  qty  INT NOT NULL DEFAULT 0
);

INSERT INTO products (sku, title, qty) VALUES
('SKU-001', 'Widget', 3),
('SKU-002', 'Gadget', 10);

-- View (harmless but helpful)
CREATE OR REPLACE VIEW v_users_emails AS
SELECT id, name, email FROM users;

-- Create low-priv app user (idempotent)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app') THEN
    CREATE ROLE app WITH LOGIN PASSWORD 'apppass';
  END IF;
END $$;

-- Grant privileges roughly equivalent to MySQL's:
--   SELECT, INSERT, UPDATE, DELETE on all tables in demo.public
-- Plus required sequence privileges so INSERTs on IDENTITY columns work.
GRANT CONNECT ON DATABASE demo TO app;
GRANT USAGE, CREATE ON SCHEMA public TO app;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO app;

-- Ensure future objects get the same grants
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO app;