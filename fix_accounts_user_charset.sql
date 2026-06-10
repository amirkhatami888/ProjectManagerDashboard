-- Fix accounts_user table charset so province (and other text fields) accept Persian/UTF-8.
-- Run this in your project database (e.g. ufvuikiv_project_manager_db) if you get:
--   Incorrect string value: '...' for column 'accounts_user'.'province'

-- Option 1: Convert the whole table (recommended)
ALTER TABLE accounts_user CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Option 2: If you only want to fix the province column:
-- ALTER TABLE accounts_user MODIFY province VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL;
