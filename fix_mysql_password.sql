-- MySQL commands to fix root password
-- Run these commands in MySQL:

-- Option 1: If you can still connect with old password or no password
ALTER USER 'root'@'localhost' IDENTIFIED BY 'Amir137667318@';
FLUSH PRIVILEGES;

-- Option 2: If you need to reset for all root users
ALTER USER 'root'@'localhost' IDENTIFIED BY 'Amir137667318@';
ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY 'Amir137667318@';
ALTER USER 'root'@'%' IDENTIFIED BY 'Amir137667318@';
FLUSH PRIVILEGES;

-- Verify the password works
SELECT user, host FROM mysql.user WHERE user='root';


