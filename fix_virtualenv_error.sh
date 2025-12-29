#!/bin/bash
# Fix virtualenv error in cPanel by checking and cleaning up virtualenv

echo "Checking virtualenv setup..."
echo ""

# Check if virtualenv directory exists
VENV_PATH="$HOME/virtualenv/public_html/PMD"
if [ -d "$VENV_PATH" ]; then
    echo "Found virtualenv at: $VENV_PATH"
    echo ""
    echo "Listing contents:"
    ls -la "$VENV_PATH"
    echo ""
    read -p "Do you want to remove this virtualenv? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        echo "Removing virtualenv..."
        rm -rf "$VENV_PATH"
        echo "✅ Virtualenv removed"
        echo ""
        echo "Now recreate your Python app in cPanel and it will create a fresh virtualenv"
    else
        echo "Keeping virtualenv. Make sure cPanel Python app is configured correctly."
    fi
else
    echo "No virtualenv found at: $VENV_PATH"
    echo "This is normal if you haven't set up the Python app yet."
fi

echo ""
echo "For cPanel Python App setup, use:"
echo "  Application root: public_html/PMD/ProjectManagerDashboard"
echo "  Application startup file: passenger_wsgi.py"
echo "  Application Entry point: application"
echo ""
echo "After setup, activate the virtualenv with:"
echo "  source ~/virtualenv/public_html/PMD/3.10/bin/activate"
echo "  (Replace 3.10 with your Python version)"

