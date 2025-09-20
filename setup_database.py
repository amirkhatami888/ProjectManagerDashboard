#!/usr/bin/env python
"""
Setup database and user for Project Manager Dashboard
"""
import mysql.connector
from mysql.connector import Error

def setup_database():
    """Setup database and user"""
    connection = None
    cursor = None
    
    try:
        # Try to connect as root (you may need to adjust the password)
        print("Attempting to connect to MySQL as root...")
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password=''  # Try empty password first
        )
        
        if connection.is_connected():
            print("✅ Connected to MySQL as root")
            cursor = connection.cursor()
            
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS project_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database 'project_manager_db' created/verified")
            
            # Create user
            cursor.execute("DROP USER IF EXISTS 'amirkhatatmi888'@'localhost'")
            cursor.execute("CREATE USER 'amirkhatatmi888'@'localhost' IDENTIFIED BY 'Amir137667318@!'")
            cursor.execute("GRANT ALL PRIVILEGES ON project_manager_db.* TO 'amirkhatatmi888'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            print("✅ User 'amirkhatatmi888' created with privileges")
            
    except Error as e:
        print(f"❌ Error with empty password: {e}")
        
        # Try with the password from the original config
        try:
            if connection:
                connection.close()
            
            print("Trying with password 'Amir137667318@'...")
            connection = mysql.connector.connect(
                host='localhost',
                port=3306,
                user='root',
                password='Amir137667318@'
            )
            
            if connection.is_connected():
                print("✅ Connected to MySQL as root with password")
                cursor = connection.cursor()
                
                # Create database
                cursor.execute("CREATE DATABASE IF NOT EXISTS project_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print("✅ Database 'project_manager_db' created/verified")
                
                # Create user
                cursor.execute("DROP USER IF EXISTS 'amirkhatatmi888'@'localhost'")
                cursor.execute("CREATE USER 'amirkhatatmi888'@'localhost' IDENTIFIED BY 'Amir137667318@!'")
                cursor.execute("GRANT ALL PRIVILEGES ON project_manager_db.* TO 'amirkhatatmi888'@'localhost'")
                cursor.execute("FLUSH PRIVILEGES")
                print("✅ User 'amirkhatatmi888' created with privileges")
                
        except Error as e2:
            print(f"❌ Error with password: {e2}")
            print("\nPlease check your MySQL installation and root password.")
            print("You may need to:")
            print("1. Start MySQL service")
            print("2. Reset root password")
            print("3. Or provide the correct root password")
            
    finally:
        if connection and connection.is_connected():
            if cursor:
                cursor.close()
            connection.close()
            print("MySQL connection closed")

if __name__ == "__main__":
    setup_database()
