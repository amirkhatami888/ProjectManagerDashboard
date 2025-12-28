#!/bin/bash
# Simple fix for auth_permission table charset

cd ~/public_html/PMD/ProjectManagerDashboard

echo "Fixing auth_permission table charset..."

mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' ufvuikiv_project_manager_db << 'EOF'
-- Fix auth_permission table
ALTER TABLE auth_permission CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE auth_permission MODIFY name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE auth_permission MODIFY codename VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

-- Fix django_content_type table
ALTER TABLE django_content_type CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE django_content_type MODIFY app_label VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE django_content_type MODIFY model VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

SELECT 'Charset fix completed!' AS status;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Charset fixed!"
    echo "Now try creating a superuser or accessing the admin to test:"
    echo "python manage.py createsuperuser"
else
    echo "❌ Error. Try running the SQL commands manually."
fi

