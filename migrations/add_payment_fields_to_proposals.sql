-- Migration: Add payment fields to proposals table
-- Date: 2026-03-29
-- Description: Add prepayment functionality to proposal system

-- Add payment-related columns
ALTER TABLE proposals
ADD COLUMN payment_status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING, CONFIRMED',
ADD COLUMN payment_deadline DATETIME NOT NULL COMMENT 'Payment deadline (creation time + 24 hours)',
ADD COLUMN depositor_name VARCHAR(50) NULL COMMENT 'Name of the depositor',
ADD COLUMN payment_confirmed_at DATETIME NULL COMMENT 'Payment confirmation timestamp',
ADD COLUMN payment_confirmed_by BIGINT NULL COMMENT 'Admin user ID who confirmed payment',
ADD CONSTRAINT fk_proposals_payment_confirmed_by FOREIGN KEY (payment_confirmed_by) REFERENCES users(id);

-- Update existing proposals to have payment_deadline
-- Set payment_deadline to created_at + 24 hours for existing records
UPDATE proposals
SET payment_deadline = DATE_ADD(created_at, INTERVAL 24 HOUR)
WHERE payment_deadline IS NULL;

-- Update enum values for status column (if using ENUM type)
-- Note: This depends on your MySQL version and current ENUM definition
-- You may need to adjust this based on your actual schema

-- Option 1: If status is ENUM, modify it
-- ALTER TABLE proposals MODIFY COLUMN status ENUM('PENDING_PAYMENT', 'POSTED', 'OFFERED', 'MATCHED', 'CANCELLED') NOT NULL DEFAULT 'PENDING_PAYMENT';

-- Option 2: If status is VARCHAR (current implementation), no change needed
-- The application code will handle the new PENDING_PAYMENT status

-- Add index on payment_status for faster queries
CREATE INDEX idx_proposals_payment_status ON proposals(payment_status);

-- Add index on payment_deadline for faster expiration checks
CREATE INDEX idx_proposals_payment_deadline ON proposals(payment_deadline);

-- Add composite index for expired proposal queries
CREATE INDEX idx_proposals_pending_payment_expired ON proposals(status, payment_status, payment_deadline);
