#!/usr/bin/env python
"""
Fix decimal.InvalidOperation error with MariaDB/MySQLdb
This script tests the connection and provides a workaround
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
django.setup()

from django.db import connection
from django.conf import settings

print("=" * 60)
print("Testing Database Connection (with MariaDB fix)")
print("=" * 60)

# Test direct MySQL connection
try:
    import MySQLdb
    
    db_config = settings.DATABASES['default']
    print(f"\n📋 Connecting to database...")
    print(f"   Database: {db_config['NAME']}")
    print(f"   User: {db_config['USER']}")
    print(f"   Host: {db_config['HOST']}")
    
    # Test direct connection
    conn = MySQLdb.connect(
        host=db_config['HOST'],
        user=db_config['USER'],
        passwd=db_config['PASSWORD'],
        db=db_config['NAME'],
        charset='utf8mb4',
        use_unicode=True
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    print(f"✅ Direct connection successful!")
    print(f"📊 Server Version: {version}")
    
    cursor.close()
    conn.close()
    
    # Now test Django connection
    print(f"\n🔌 Testing Django connection...")
    connection.ensure_connection()
    print("✅ Django connection successful!")
    
    # Test a simple query
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✅ Query test successful: {result}")
    
    print("\n✅ All tests passed! Database is ready for migrations.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n🔧 Possible solutions:")
    print("   1. Check .env file exists and has correct values")
    print("   2. Verify database exists")
    print("   3. Try updating MySQLdb: pip install --upgrade mysqlclient")
    print("   4. Check if using MariaDB (may need different driver)")
    import traceback
    traceback.print_exc()
    sys.exit(1)

