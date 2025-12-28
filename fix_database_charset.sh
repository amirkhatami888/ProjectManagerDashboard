#!/bin/bash
# Fix database charset to support Persian text

cd ~/public_html/PMD/ProjectManagerDashboard

echo "Fixing database charset to utf8mb4..."

mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' ufvuikiv_project_manager_db << 'EOF'
-- Convert database to utf8mb4
ALTER DATABASE ufvuikiv_project_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Convert all tables to utf8mb4
SET FOREIGN_KEY_CHECKS = 0;

-- Get list of all tables and convert them
SET @tables = NULL;
SELECT GROUP_CONCAT('`', table_name, '`') INTO @tables
FROM information_schema.tables
WHERE table_schema = 'ufvuikiv_project_manager_db'
AND table_type = 'BASE TABLE';

SET @tables = CONCAT('ALTER TABLE ', @tables, ' CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci');

PREPARE stmt FROM @tables;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET FOREIGN_KEY_CHECKS = 1;

-- Specifically fix auth_permission table (the one causing the error)
ALTER TABLE auth_permission CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE auth_permission MODIFY name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE auth_permission MODIFY content_type_id INT NOT NULL;
ALTER TABLE auth_permission MODIFY codename VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

-- Fix other common Django tables
ALTER TABLE django_content_type CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE django_content_type MODIFY app_label VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE django_content_type MODIFY model VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

ALTER TABLE django_migrations CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE django_migrations MODIFY app VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE django_migrations MODIFY name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

SELECT 'Database charset conversion completed!' AS status;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database charset fixed!"
    echo "Now run migrations again:"
    echo "python manage.py migrate"
else
    echo "❌ Error fixing charset. Check MySQL connection."
fi

