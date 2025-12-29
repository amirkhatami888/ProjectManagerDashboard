#!/bin/bash
# Clean Python cache files and pull from git

cd ~/public_html/PMD/ProjectManagerDashboard

echo "Cleaning Python cache files..."

# Remove all __pycache__ directories
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true

# Remove .pyc files
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Remove .pyo files
find . -type f -name "*.pyo" -delete 2>/dev/null || true

echo "✅ Cache files cleaned!"
echo ""
echo "Pulling from git..."

# Stash any other local changes (if any)
git stash

# Pull from main
git pull origin main

echo ""
echo "✅ Done!"

