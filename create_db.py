import mysql.connector
from mysql.connector import Error

connection = None
cursor = None

try:
    connection = mysql.connector.connect(
        host='localhost',
        port=3306,  # Changed to standard MySQL port
        user='root',
        password='Amir137667318@'
    )
    
    if connection.is_connected():
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS project_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("Database 'project_manager_db' created successfully!")
        
except Error as e:
    print(f"Error: {e}")
    
finally:
    if connection and connection.is_connected():
        if cursor:
            cursor.close()
        connection.close()
        print("MySQL connection is closed") 