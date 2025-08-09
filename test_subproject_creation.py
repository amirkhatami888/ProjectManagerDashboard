#!/usr/bin/env python
"""
Simple test script to verify subproject creation works after fixing executive_stage field issue
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProjectManagerDashboard.settings')
django.setup()

from creator_project.models import Project
from creator_subproject.models import SubProject
from accounts.models import User
from django.utils import timezone

def test_subproject_creation():
    """Test creating a subproject to verify the executive_stage field issue is fixed"""
    print("Testing subproject creation...")
    
    try:
        # Get or create a test user
        test_user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            print(f"✅ Created test user: {test_user.username}")
        else:
            print(f"✅ Using existing test user: {test_user.username}")
        
        # Get or create a test project
        test_project, created = Project.objects.get_or_create(
            name='Test Project for SubProject Creation',
            defaults={
                'created_by': test_user,
                'project_type': 'مسجد',
                'overall_status': 'فعال',
                'physical_progress': 0,
                'max_subprojects': 5
            }
        )
        if created:
            print(f"✅ Created test project: {test_project.name}")
        else:
            print(f"✅ Using existing test project: {test_project.name}")
        
        # Try to create a subproject
        test_subproject = SubProject(
            project=test_project,
            name='Test SubProject',
            sub_project_type='فاز مطالعاتی',  # Using one of the valid choices
            sub_project_number=1,
            is_suportting_charity='ندارد',
            created_by=test_user,
            state='فعال',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
            imagenary_duration=30
        )
        
        # This should work without the executive_stage error
        test_subproject.save()
        print(f"✅ Successfully created subproject: {test_subproject}")
        
        # Clean up - delete the test subproject
        test_subproject.delete()
        print("✅ Cleaned up test subproject")
        
        # Also clean up test project if we created it
        if created:
            test_project.delete()
            print("✅ Cleaned up test project")
            
        print("\n🎉 SUCCESS: Subproject creation is working properly!")
        print("The executive_stage field error has been fixed.")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = test_subproject_creation()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
