#!/usr/bin/env python
"""
Script to set up MySQL database on Windows VPS
"""
import os
import sys
import subprocess
import MySQLdb

def check_mysql_installation():
    """Check if MySQL is installed and running"""
    try:
        result = subprocess.run(['mysql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MySQL is installed:", result.stdout.strip())
            return True
        else:
            print("❌ MySQL is not installed or not in PATH")
            return False
    except FileNotFoundError:
        print("❌ MySQL command not found. Please install MySQL first.")
        return False

def create_database():
    """Create the project database"""
    try:
        # Get database credentials from environment or use defaults
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', '')
        db_name = os.getenv('DB_NAME', 'project_manager_db')
        
        print(f"🔗 Connecting to MySQL as user: {db_user}")
        
        # Connect to MySQL server
        connection = MySQLdb.connect(
            host='localhost',
            user=db_user,
            passwd=db_password,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Create database
        print(f"📊 Creating database: {db_name}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        # Show databases
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print("📋 Available databases:")
        for db in databases:
            print(f"   - {db[0]}")
        
        print(f"✅ Database '{db_name}' created successfully!")
        
        # Test connection to the new database
        cursor.execute(f"USE {db_name}")
        cursor.execute("SELECT 1")
        print("✅ Database connection test successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
            print("🔒 MySQL connection closed")

def check_python_dependencies():
    """Check if required Python packages are installed"""
    required_packages = ['Django', 'mysqlclient', 'python-decouple']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is not installed")
    
    if missing_packages:
        print(f"\n📦 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def test_django_connection():
    """Test Django database connection"""
    try:
        import django
        from django.conf import settings
        from django.core.management import execute_from_command_line
        
        # Set Django settings module
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')
        
        # Setup Django
        django.setup()
        
        # Test database connection
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        if result:
            print("✅ Django database connection successful!")
            return True
        else:
            print("❌ Django database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Django connection test failed: {e}")
        return False

def main():
    print("🚀 Windows VPS MySQL Setup for Project Manager Dashboard")
    print("=" * 60)
    
    # Check MySQL installation
    if not check_mysql_installation():
        print("\n📋 Please install MySQL first:")
        print("1. Download from: https://dev.mysql.com/downloads/mysql/")
        print("2. Install MySQL Community Server")
        print("3. Start MySQL service")
        return
    
    # Check Python dependencies
    print("\n🔍 Checking Python dependencies...")
    if not check_python_dependencies():
        return
    
    # Create database
    print("\n🗄️  Setting up database...")
    if not create_database():
        return
    
    # Test Django connection
    print("\n🧪 Testing Django connection...")
    if not test_django_connection():
        print("\n📋 Next steps:")
        print("1. Check your .env file configuration")
        print("2. Run: python manage.py migrate")
        print("3. Run: python manage.py createsuperuser")
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run: python manage.py migrate")
    print("2. Run: python manage.py createsuperuser")
    print("3. Run: python manage.py collectstatic")
    print("4. Configure IIS for deployment")

if __name__ == "__main__":
    main()
