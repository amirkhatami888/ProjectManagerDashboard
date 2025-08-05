from django.core.management.base import BaseCommand
from creator_subproject.models import SubProject


class Command(BaseCommand):
    help = 'Updates all subproject relationships and recalculates dates'

    def handle(self, *args, **options):
        # Get all subprojects that have relationship information
        subprojects = SubProject.objects.filter(related_subproject__isnull=False)
        
        self.stdout.write(f"Found {subprojects.count()} subprojects with relationships to update")
        
        # First pass: recalculate dates for all related subprojects
        for subproject in subprojects:
            try:
                original_start = subproject.start_date
                original_end = subproject.end_date
                
                # Recalculate dates based on relationship
                subproject.calculate_dates()
                subproject.save(update_fields=['start_date', 'end_date'])
                
                # Report changes
                self.stdout.write(f"Updated subproject {subproject.id} ({subproject.name})")
                self.stdout.write(f"  Relationship: {subproject.relationship_type} with {subproject.related_subproject.name}")
                self.stdout.write(f"  Start date changed: {original_start} -> {subproject.start_date}")
                self.stdout.write(f"  End date changed: {original_end} -> {subproject.end_date}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error updating subproject {subproject.id}: {str(e)}"))
        
        # Second pass: update dependent subprojects
        for subproject in SubProject.objects.filter(related_subproject__isnull=False):
            try:
                # Find all dependent subprojects
                dependent_projects = SubProject.objects.filter(related_subproject=subproject)
                for dep in dependent_projects:
                    original_start = dep.start_date
                    original_end = dep.end_date
                    
                    # Recalculate dates based on relationship
                    dep.calculate_dates()
                    dep.save(update_fields=['start_date', 'end_date'])
                    
                    # Report changes
                    self.stdout.write(f"Updated dependent subproject {dep.id} ({dep.name})")
                    self.stdout.write(f"  Start date changed: {original_start} -> {dep.start_date}")
                    self.stdout.write(f"  End date changed: {original_end} -> {dep.end_date}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error updating dependent subprojects for {subproject.id}: {str(e)}"))
                
        self.stdout.write(self.style.SUCCESS("Successfully updated all subproject relationships")) 