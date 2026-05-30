-- OrderRun Database Initialization Script
-- This script runs automatically when the MySQL container is first created.

USE orderrun;

-- Keep local test database available for integration-test workflows.
CREATE DATABASE IF NOT EXISTS orderrun_test;

SELECT 'OrderRun database initialized successfully' AS message;
SELECT 'OrderRun test database created' AS message;
