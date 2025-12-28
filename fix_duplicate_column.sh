#!/bin/bash
# Fix duplicate column error - check if column exists and handle it

cd ~/public_html/PMD/ProjectManagerDashboard

echo "Checking if province column exists..."

# Check if column exists
mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' ufvuikiv_project_manager_db << 'EOF'
SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_DEFAULT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'ufvuikiv_project_manager_db' 
AND TABLE_NAME = 'creator_program_program' 
AND COLUMN_NAME = 'province';
EOF

echo ""
echo "If column exists, we need to either:"
echo "1. Mark migration as fake (if column is correct)"
echo "2. Drop and recreate the column"
echo ""
echo "Let's check the current state and fix it..."

# Check current state
COLUMN_EXISTS=$(mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' ufvuikiv_project_manager_db -sN -e "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'ufvuikiv_project_manager_db' AND TABLE_NAME = 'creator_program_program' AND COLUMN_NAME = 'province';")

if [ "$COLUMN_EXISTS" = "1" ]; then
    echo "✅ Column exists. Checking if it needs to be fixed..."
    
    # Check if column is nullable
    IS_NULLABLE=$(mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' ufvuikiv_project_manager_db -sN -e "SELECT IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'ufvuikiv_project_manager_db' AND TABLE_NAME = 'creator_program_program' AND COLUMN_NAME = 'province';")
    
    if [ "$IS_NULLABLE" = "YES" ]; then
        echo "Column is nullable. Fixing it..."
        mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' ufvuikiv_project_manager_db << 'EOF'
        -- Update NULL values
        UPDATE creator_program_program SET province = 'تهران' WHERE province IS NULL;
        -- Alter column to NOT NULL with default
        ALTER TABLE creator_program_program MODIFY COLUMN province VARCHAR(50) NOT NULL DEFAULT 'تهران';
EOF
        echo "✅ Column fixed! Now mark migration as applied:"
        echo "python manage.py migrate creator_program 0002 --fake"
    else
        echo "Column already exists and is NOT NULL. Marking migration as applied:"
        python manage.py migrate creator_program 0002 --fake
    fi
else
    echo "Column doesn't exist. Running normal migration..."
    python manage.py migrate
fi

