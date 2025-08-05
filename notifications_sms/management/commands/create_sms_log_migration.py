from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Create a migration file to add message_id field to SMSLog model'

    def handle(self, *args, **options):
        # Migration content
        migration_content = """from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('notifications_sms', '0002_add_created_at_to_smstemplate'),  # Update this to match your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='smslog',
            name='message_id',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Message ID'),
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
        migration_filename = f"{new_num:04d}_add_message_id_to_smslog.py"
        with open(os.path.join(migrations_dir, migration_filename), 'w') as f:
            f.write(migration_content)
            
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created migration {migration_filename}')
        ) 