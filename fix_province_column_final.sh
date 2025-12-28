#!/bin/bash
# Final fix for province column - disable strict mode temporarily

cd ~/public_html/PMD/ProjectManagerDashboard

echo "Fixing province column..."

# Fix the column by temporarily disabling strict mode
mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' ufvuikiv_project_manager_db << 'EOF'
-- Temporarily disable strict mode
SET SESSION sql_mode = '';

-- Update NULL values
UPDATE creator_program_program SET province = 'تهران' WHERE province IS NULL;

-- Fix the column (make it NOT NULL with default)
ALTER TABLE creator_program_program MODIFY COLUMN province VARCHAR(50) NOT NULL DEFAULT 'تهران';

-- Re-enable strict mode
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
EOF

if [ $? -eq 0 ]; then
    echo "✅ Column fixed successfully!"
    echo "Now marking migration as applied..."
    python manage.py migrate creator_program 0002 --fake
    echo "✅ Migration marked as applied!"
    echo "Continuing with remaining migrations..."
    python manage.py migrate
else
    echo "❌ Error fixing column. Check MySQL connection and permissions."
fi

