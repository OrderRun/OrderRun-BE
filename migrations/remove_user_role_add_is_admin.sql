-- Migration: Remove role field and add is_admin to users table
-- Date: 2026-03-29
-- Description: Change user role system from enum to relationship-based roles (Orderer/Runner)
--              Admin role becomes a boolean flag instead of enum value

-- Step 1: Add is_admin column with default value
ALTER TABLE users
ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Whether user is an admin';

-- Step 2: Migrate existing admin users (if role column exists and contains 'admin')
-- Note: This step is only needed if you have existing data with role='admin'
-- UPDATE users SET is_admin = TRUE WHERE role = 'admin';

-- Step 3: Remove the role column
-- Note: Uncomment this after verifying the migration is successful
-- ALTER TABLE users DROP COLUMN role;

-- Step 4: Add index on is_admin for faster admin queries
CREATE INDEX idx_users_is_admin ON users(is_admin);

-- Business Rules After Migration:
-- 1. User roles are now determined by relationships:
--    - Orderer: User who creates Proposals (Proposal.orderer_id)
--    - Runner: User who submits Offers (Offer.runner_id)
-- 2. A single user can be both an orderer and a runner
-- 3. Orderers cannot submit offers to their own proposals (enforced at application level)
-- 4. Only is_admin flag determines admin privileges
