#!/bin/bash
# Fix duplicate passenger_wsgi.py files

cd ~/public_html/PMD

echo "Checking passenger_wsgi.py files..."
echo ""

# Check the file in PMD directory
if [ -f "passenger_wsgi.py" ]; then
    echo "Found passenger_wsgi.py in PMD directory:"
    ls -la passenger_wsgi.py
    echo ""
    echo "Content:"
    head -5 passenger_wsgi.py
    echo ""
    read -p "Delete this file? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        rm passenger_wsgi.py
        echo "✅ Deleted passenger_wsgi.py from PMD directory"
    else
        echo "Keeping the file. Make sure cPanel points to ProjectManagerDashboard/passenger_wsgi.py"
    fi
else
    echo "No passenger_wsgi.py in PMD directory (good!)"
fi

echo ""
echo "Correct file location:"
ls -la ProjectManagerDashboard/passenger_wsgi.py

echo ""
echo "For cPanel, use:"
echo "  App Directory: public_html/PMD/ProjectManagerDashboard"
echo "  Application startup file: passenger_wsgi.py"
echo "  Application Entry point: application"

