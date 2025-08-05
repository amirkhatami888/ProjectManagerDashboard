#!/usr/bin/env python
"""
Simple script to set up UTF8MB4 Unicode collation using Django's database connection.
This script will:
1. Set up Django with production settings
2. Run the UTF8MB4 collation management command
3. Apply migrations
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_utf8mb4():
    """Set up UTF8MB4 collation using Django"""
    print("🚀 Setting up UTF8MB4 Unicode collation...")
    print("=" * 50)
    
    try:
        # Set up Django with production settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
        django.setup()
        
        print("✅ Django setup completed")
        
        # Run migrations first
        print("\n📋 Step 1: Running Django migrations...")
        os.system("python manage.py migrate")
        print("✅ Migrations completed")
        
        # Run the UTF8MB4 collation setup
        print("\n📋 Step 2: Setting up UTF8MB4 collation...")
        os.system("python manage.py setup_utf8mb4_collation")
        print("✅ UTF8MB4 collation setup completed")
        
        print("\n" + "=" * 50)
        print("🎉 UTF8MB4 Unicode collation setup completed successfully!")
        print("\n📝 Your database is now configured to support:")
        print("   • Persian/Farsi text")
        print("   • Arabic text")
        print("   • Emojis and special characters")
        print("   • Full Unicode support")
        print("\n🔧 Next steps:")
        print("   1. Restart your Django application")
        print("   2. Test with Persian text input")
        print("   3. Verify emoji support if needed")
        
    except Exception as e:
        print(f"❌ Error setting up UTF8MB4: {e}")
        print("\n💡 Make sure:")
        print("   • MySQL server is running")
        print("   • Database credentials are correct")
        print("   • Database exists with UTF8MB4 collation")

if __name__ == '__main__':
    setup_utf8mb4() 