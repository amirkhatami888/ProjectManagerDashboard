#!/bin/bash
# Test different path formats for cPanel

echo "Testing cPanel path resolution..."
echo ""

BASE_DIR="/home/ufvuikiv"
PROJECT_DIR="public_html/PMD/ProjectManagerDashboard"
FILE="passenger_wsgi.py"

echo "File location:"
echo "$BASE_DIR/$PROJECT_DIR/$FILE"
echo ""

echo "If cPanel base is: public_html/PMD/"
echo "Then App Directory should be: ProjectManagerDashboard"
echo "Full path would be: $BASE_DIR/public_html/PMD/ProjectManagerDashboard/$FILE"
echo ""

echo "If cPanel base is: public_html/"
echo "Then App Directory should be: PMD/ProjectManagerDashboard"
echo "Full path would be: $BASE_DIR/public_html/PMD/ProjectManagerDashboard/$FILE"
echo ""

echo "If cPanel base is: ~/"
echo "Then App Directory should be: public_html/PMD/ProjectManagerDashboard"
echo "Full path would be: $BASE_DIR/public_html/PMD/ProjectManagerDashboard/$FILE"
echo ""

echo "Try these App Directory values in order:"
echo "  1. ProjectManagerDashboard"
echo "  2. PMD/ProjectManagerDashboard"
echo "  3. public_html/PMD/ProjectManagerDashboard"
echo "  4. /home/ufvuikiv/public_html/PMD/ProjectManagerDashboard"
echo ""
echo "Application startup file: passenger_wsgi.py"
echo "Application Entry point: application"

