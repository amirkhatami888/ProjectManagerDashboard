from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Create a migration file to add created_at field to SMSTemplate model'

    def handle(self, *args, **options):
        # Migration content
        migration_content = """from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [
        ('notifications_sms', '0001_initial'),  # Update this if needed
    ]

    operations = [
        migrations.AddField(
            model_name='smstemplate',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='smstemplate',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
"""
        
        # Create migrations directory if it doesn't exist
        migrations_dir = 'notifications_sms/migrations/'
        os.makedirs(migrations_dir, exist_ok=True)
        
        # Find the highest migration number
        existing_migrations = [f for f in os.listdir(migrations_dir) 
                              if f.endswith('.py') and f != '__init__.py']
        
        if existing_migrations:
            highest_num = max([int(f.split('_')[0]) for f in existing_migrations 
                              if f.split('_')[0].isdigit()])
            new_num = highest_num + 1
        else:
            new_num = 1
            
        # Create new migration file
        migration_filename = f"{new_num:04d}_add_created_at_to_smstemplate.py"
        with open(os.path.join(migrations_dir, migration_filename), 'w') as f:
            f.write(migration_content)
            
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created migration {migration_filename}')
        ) 