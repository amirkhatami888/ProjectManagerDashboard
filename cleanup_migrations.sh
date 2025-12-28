#!/bin/bash
# Remove conflicting migration file

cd ~/public_html/PMD/ProjectManagerDashboard/creator_program/migrations

if [ -f "0002_program_province_fixed.py" ]; then
    echo "Removing conflicting migration file..."
    rm 0002_program_province_fixed.py
    echo "✅ Removed 0002_program_province_fixed.py"
else
    echo "No conflicting file found."
fi

echo "Migration files:"
ls -la 0*.py

