#!/bin/bash

# Nginx deployment script for Django Project Manager Dashboard

echo "Starting nginx deployment..."

# Create error pages directory if it doesn't exist
mkdir -p /home/amirho10/public_html/ProjectManagerDashboard/error_pages

# Copy error pages to server
cp error_pages/404.html /home/amirho10/public_html/ProjectManagerDashboard/error_pages/
cp error_pages/50x.html /home/amirho10/public_html/ProjectManagerDashboard/error_pages/

# Set proper permissions
chmod 644 /home/amirho10/public_html/ProjectManagerDashboard/error_pages/*.html

# Copy nginx configuration
cp nginx.conf /etc/nginx/sites-available/project_manager_dashboard

# Create symbolic link to enable site
ln -sf /etc/nginx/sites-available/project_manager_dashboard /etc/nginx/sites-enabled/

# Test nginx configuration
nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid. Reloading nginx..."
    systemctl reload nginx
    echo "Nginx deployment completed successfully!"
else
    echo "Nginx configuration test failed. Please check the configuration."
    exit 1
fi

# Start Django application with waitress
echo "Starting Django application..."
cd /home/amirho10/public_html/ProjectManagerDashboard
python server.py &

echo "Deployment completed!"
