-- Demo schema and seed data for SQLi testbed
-- Note: This file is mounted into MySQL init directory by docker-compose

DROP DATABASE IF EXISTS demo;
CREATE DATABASE demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE demo;

-- Users table
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
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
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  color VARCHAR(50) NOT NULL,
  price DECIMAL(10,2) NOT NULL DEFAULT 0.00
);

INSERT INTO fruit (name, color, price) VALUES
('apple', 'red', 1.20),
('banana', 'yellow', 0.80),
('pear', 'green', 1.10);

-- Products table
CREATE TABLE products (
  id INT PRIMARY KEY AUTO_INCREMENT,
  sku VARCHAR(64) NOT NULL,
  title VARCHAR(255) NOT NULL,
  qty INT NOT NULL DEFAULT 0
);

INSERT INTO products (sku, title, qty) VALUES
('SKU-001', 'Widget', 3),
('SKU-002', 'Gadget', 10);

-- Create a view to show cross-table info (harmless but helpful)
CREATE VIEW v_users_emails AS
  SELECT id, name, email FROM users;

-- Make sure information_schema is visible by default (it is) but create a low-priv user for apps
CREATE USER IF NOT EXISTS 'app'@'%' IDENTIFIED BY 'apppass';
GRANT SELECT, INSERT, UPDATE, DELETE, SHOW VIEW ON demo.* TO 'app'@'%';
FLUSH PRIVILEGES;


