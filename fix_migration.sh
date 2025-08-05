#!/bin/bash

# Script to fix migration history on production server
# Run this script on the production server

echo "Fixing migration history on production server..."

# Navigate to the project directory
cd /home/amirho10/public_html/ProjectManagerDashboard

# Run the Python script to fix the migration
python production_migration_fix.py

echo "Migration fix completed." 