#!/usr/bin/env python
"""
Test DB connection (MariaDB/decimal-safe).
Uses PyMySQL so DECIMAL columns don't trigger decimal.ConversionSyntax.
"""
import os
import sys

# Use PyMySQL as MySQLdb before Django loads (avoids decimal.InvalidOperation)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
django.setup()

from django.db import connection
from django.conf import settings

def main():
    print("=" * 60)
    print("Testing Database Connection (MariaDB / PyMySQL)")
    print("=" * 60)

    db_config = settings.DATABASES['default']
    print("\nConnecting to database...")
    print("   Database:", db_config['NAME'])
    print("   User:", db_config['USER'])
    print("   Host:", db_config['HOST'])

    try:
        connection.ensure_connection()
        print("Django connection OK.")

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("Query test OK:", result)
            cursor.execute("SELECT @@version")
            row = cursor.fetchone()
            if row:
                print("Server version:", row[0])
        print("\nAll tests passed. Database is ready.")
    except Exception as e:
        print("\nError:", e)
        print("Check .env, DB credentials, and that PyMySQL is installed.")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

