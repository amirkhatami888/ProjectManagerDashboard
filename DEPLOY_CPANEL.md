# cPanel Deployment Instructions

## Quick Setup Steps

### 1. Create .env file on cPanel server

SSH into your cPanel server and run:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" > /tmp/secret_key.txt
SECRET_KEY=$(cat /tmp/secret_key.txt)
rm /tmp/secret_key.txt

cat > .env << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
DJANGO_SETTINGS_MODULE=project_dashboard.production_settings
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_ENGINE=django.db.backends.mysql
DB_NAME=ufvuikiv_project_manager_db
DB_USER=ufvuikiv_amirkhatatmi888
DB_PASSWORD=Amir137667318@
DB_HOST=localhost
DB_PORT=3306
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
EOF

chmod 600 .env
```

**IMPORTANT:** Replace `yourdomain.com` with your actual domain name!

### 2. Verify database exists

```bash
mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' -e "SHOW DATABASES LIKE 'ufvuikiv_project_manager_db';"
```

If database doesn't exist, create it:

```bash
mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' -e "CREATE DATABASE IF NOT EXISTS ufvuikiv_project_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 3. Run migrations

```bash
cd ~/public_html/PMD/ProjectManagerDashboard
source ~/virtualenv/public_html/PMD/3.10/bin/activate
python manage.py migrate
```

### 4. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 5. Create superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Set file permissions

```bash
chmod 755 media logs
chmod 644 .env
```

### 7. Restart Python app in cPanel

Go to cPanel → Setup Python App → Click "Restart" for your application.

## Troubleshooting

### If you get "Unknown database" error:
- Verify database exists: `mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' -e "SHOW DATABASES;"`
- Create database if missing (see step 2 above)

### If you get "Access denied" error:
- Verify MySQL credentials in .env file
- Check user has permissions: `mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' -e "SHOW GRANTS;"`
- Grant permissions if needed: `GRANT ALL PRIVILEGES ON ufvuikiv_project_manager_db.* TO 'ufvuikiv_amirkhatatmi888'@'localhost'; FLUSH PRIVILEGES;`

### If you get decimal.InvalidOperation error:
- This usually means database connection issue
- Check .env file exists and has correct values
- Verify database credentials are correct
- Make sure database exists

### Check logs:
```bash
tail -f logs/django.log
```

