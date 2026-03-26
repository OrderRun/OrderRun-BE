-- OrderRun Database Initialization Script
-- This script runs automatically when the MySQL container is first created

-- Ensure we're using the correct database
USE orderrun;

-- Set timezone
SET time_zone = '+09:00';

-- Create test database for integration tests
CREATE DATABASE IF NOT EXISTS orderrun_test;

-- Create indexes for better performance (tables will be created by Alembic migrations)
-- This file is kept minimal; schema creation is handled by SQLAlchemy + Alembic

-- Initial setup complete
SELECT 'OrderRun database initialized successfully' AS message;
SELECT 'OrderRun test database created' AS message;
