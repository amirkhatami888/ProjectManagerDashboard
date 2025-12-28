# Fix: decimal.InvalidOperation Error

## Problem

You're getting `decimal.InvalidOperation: [<class 'decimal.ConversionSyntax'>]` when running `python manage.py migrate`.

This is a known compatibility issue between MySQLdb and MariaDB when Django tries to check the database version.

## Solution 1: Update Database Configuration (Already Applied)

I've updated `production_settings.py` with additional database options that should fix this issue.

## Solution 2: Upgrade MySQLdb/mysqlclient

Try upgrading the MySQL client library:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard
source ~/virtualenv/public_html/PMD/3.10/bin/activate
pip install --upgrade mysqlclient
```

## Solution 3: Use PyMySQL Instead (Alternative)

If MySQLdb continues to have issues, you can use PyMySQL as a drop-in replacement:

```bash
pip install pymysql
```

Then add this to the **top** of your `manage.py` file (before any Django imports):

```python
import pymysql
pymysql.install_as_MySQLdb()
```

## Solution 4: Skip Database Version Check (Temporary Workaround)

If you need to run migrations immediately, you can temporarily skip the version check by modifying Django's database backend. However, this is not recommended for production.

## Test the Fix

After applying the changes, test the connection:

```bash
python fix_decimal_error.py
```

Or test directly:

```bash
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
django.setup()
from django.db import connection
connection.ensure_connection()
print('✅ Connection successful!')
"
```

## If Still Not Working

1. **Check MariaDB version:**
   ```bash
   mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' -e "SELECT VERSION();"
   ```

2. **Try direct connection test:**
   ```bash
   python fix_decimal_error.py
   ```

3. **Check .env file:**
   ```bash
   cat .env | grep DB_
   ```

4. **Try using PyMySQL** (Solution 3 above) - it's more compatible with MariaDB

## Recommended: Use PyMySQL

For MariaDB, PyMySQL is often more reliable than MySQLdb. To switch:

1. Install PyMySQL:
   ```bash
   pip install pymysql
   ```

2. Add to `manage.py` (at the very top, before any imports):
   ```python
   import pymysql
   pymysql.install_as_MySQLdb()
   ```

3. Add to `passenger_wsgi.py` (at the very top):
   ```python
   import pymysql
   pymysql.install_as_MySQLdb()
   ```

This makes PyMySQL act as MySQLdb, which should resolve the decimal error.

