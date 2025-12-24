#!/usr/bin/env python
"""
Test MySQL connection with different password scenarios
"""
import MySQLdb
import sys

def test_connection(password):
    """Test MySQL connection with given password"""
    try:
        print(f"Testing connection with password: {password[:3]}***")
        conn = MySQLdb.connect(
            host='localhost',
            user='root',
            passwd=password,
            db='mysql'
        )
        print("✅ Connection successful!")
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"MySQL Version: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except MySQLdb.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("MySQL Connection Test")
    print("=" * 60)
    
    # Test with the password from settings
    password = "Amir137667318@"
    success = test_connection(password)
    
    if not success:
        print("\n" + "=" * 60)
        print("Troubleshooting Steps:")
        print("=" * 60)
        print("1. Make sure MySQL server is running")
        print("2. Try connecting with MySQL command line:")
        print(f"   mysql -u root -p")
        print("   (Enter password when prompted)")
        print("\n3. If connection fails, try resetting the password:")
        print("   mysql -u root -p")
        print("   (Use your current password or skip if no password)")
        print("   Then run:")
        print(f"   ALTER USER 'root'@'localhost' IDENTIFIED BY '{password}';")
        print("   FLUSH PRIVILEGES;")
        print("\n4. Verify the password works:")
        print(f"   mysql -u root -p{password} -e 'SELECT 1;'")
        sys.exit(1)
    else:
        print("\n✅ MySQL connection is working correctly!")
        print("You can now run: python manage.py migrate")


