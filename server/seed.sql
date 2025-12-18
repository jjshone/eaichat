-- MySQL Seed Data for eaichat
-- Run with: mysql -u eaichat -p eaichat < seed.sql

-- Create default admin user (password: admin123 - bcrypt hash)
INSERT INTO users (email, hashed_password, is_active, is_admin, created_at) VALUES
('admin@eaichat.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4u7F5OI5CZ7f5fLe', 1, 1, NOW()),
('user@eaichat.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4u7F5OI5CZ7f5fLe', 1, 0, NOW())
ON DUPLICATE KEY UPDATE email=email;

-- Create sample products (will be populated from Fake Store API via Python script)
-- This is just a fallback for basic testing
INSERT INTO products (title, description, price, category, created_at) VALUES
('Sample Product 1', 'A sample product for testing', 19.99, 'electronics', NOW()),
('Sample Product 2', 'Another sample product', 29.99, 'clothing', NOW()),
('Sample Product 3', 'Third sample product', 39.99, 'jewelery', NOW())
ON DUPLICATE KEY UPDATE title=title;

-- Create reindex checkpoint for products collection
INSERT INTO reindex_checkpoints (collection, last_processed_id, updated_at) VALUES
('products', 0, NOW())
ON DUPLICATE KEY UPDATE collection=collection;
