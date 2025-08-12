-- PostgreSQL demo schema
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user'
);
INSERT INTO users (name, email, role) VALUES
('alice', 'alice@example.com', 'admin'),
('bob', 'bob@example.com', 'user');


