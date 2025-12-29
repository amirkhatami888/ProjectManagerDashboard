#!/bin/bash
# Check cPanel Python app configuration

echo "Checking cPanel Python app configuration..."
echo ""

# Check for passenger_wsgi.py in common locations
echo "1. Checking passenger_wsgi.py locations:"
echo "   Home directory:"
ls -la ~/passenger_wsgi.py 2>/dev/null || echo "   ❌ Not found in ~/"
echo ""
echo "   Project directory:"
ls -la ~/public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py 2>/dev/null || echo "   ❌ Not found"
echo ""

# Check for .passenger files
echo "2. Checking for Passenger configuration files:"
find ~ -name ".passenger*" -o -name "passenger_wsgi.py" 2>/dev/null | head -10
echo ""

# Check Python app directories
echo "3. Checking Python app directories:"
ls -la ~/public_html/PMD/ 2>/dev/null | grep -E "passenger|wsgi|python"
echo ""

echo "4. Current working directory structure:"
pwd
ls -la | grep -E "passenger|manage.py"
echo ""

echo "For cPanel, try these App Directory values:"
echo "  Option A: public_html/PMD/ProjectManagerDashboard"
echo "  Option B: /home/ufvuikiv/public_html/PMD/ProjectManagerDashboard"
echo "  Option C: PMD/ProjectManagerDashboard"
echo ""
echo "Application startup file should always be: passenger_wsgi.py"
echo "Application Entry point should always be: application"

