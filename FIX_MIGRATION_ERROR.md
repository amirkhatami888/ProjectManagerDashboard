# Fix: Invalid default value for 'province' Error

## Problem

MySQL/MariaDB strict mode rejects the Persian default value `'تهران'` when adding a field to an existing table.

## Solution Applied

I've modified the migration `0002_program_province.py` to:

1. **Add field as nullable first** - This avoids the strict mode error
2. **Set default values** - Update existing rows with the default value
3. **Make field non-nullable** - Final step to match the model definition

## What to Do

The migration file has been updated. You need to:

1. **Upload the fixed migration file** to your server:
   ```bash
   # On your local machine, the file is already updated
   # Upload it to: ~/public_html/PMD/ProjectManagerDashboard/creator_program/migrations/0002_program_province.py
   ```

2. **Run migrations again**:
   ```bash
   cd ~/public_html/PMD/ProjectManagerDashboard
   source ~/virtualenv/public_html/PMD/3.10/bin/activate
   python manage.py migrate
   ```

## Alternative: Quick Fix on Server

If you can't upload the file, you can fix it directly on the server:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard/creator_program/migrations

# Backup the original
cp 0002_program_province.py 0002_program_province.py.bak

# Edit the file (use nano or vi)
nano 0002_program_province.py
```

Then change the `AddField` operation to include `null=True, blank=True`, and add the RunSQL and AlterField operations as shown in the fixed version.

## If Migration Still Fails

You can also temporarily disable strict mode:

```bash
mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' << EOF
SET SESSION sql_mode = '';
USE ufvuikiv_project_manager_db;
EOF

# Then run migration
python manage.py migrate

# Re-enable strict mode (optional)
mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' << EOF
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
EOF
```

But the migration fix is the better solution!

