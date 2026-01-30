import pymysql

# Use PyMySQL as MySQLdb to avoid mysqlclient/MariaDB decimal conversion issues
pymysql.install_as_MySQLdb()