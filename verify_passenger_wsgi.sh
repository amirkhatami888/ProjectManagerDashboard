#!/bin/bash
# Verify passenger_wsgi.py location and content

cd ~/public_html/PMD/ProjectManagerDashboard

echo "Checking passenger_wsgi.py..."
echo ""

# Check if file exists
if [ -f "passenger_wsgi.py" ]; then
    echo "✅ File exists at:"
    pwd
    echo "   passenger_wsgi.py"
    echo ""
    echo "Full path:"
    echo "$(pwd)/passenger_wsgi.py"
    echo ""
    echo "File content (first 10 lines):"
    head -10 passenger_wsgi.py
    echo ""
    echo "✅ File looks good!"
    echo ""
    echo "For cPanel, use these settings:"
    echo "  App Directory: PMD/ProjectManagerDashboard"
    echo "  Application startup file: passenger_wsgi.py"
    echo "  Application Entry point: application"
else
    echo "❌ File NOT found!"
    echo "Current directory: $(pwd)"
    echo ""
    echo "Looking for file..."
    find ~/public_html -name "passenger_wsgi.py" 2>/dev/null
fi

