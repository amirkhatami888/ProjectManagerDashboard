from django.core.management.base import BaseCommand
from creator_program.models import Program


class Command(BaseCommand):
    help = 'Calculate and populate program_opening_date for all programs based on their projects\' end dates'

    def handle(self, *args, **options):
        programs = Program.objects.all()
        updated_count = 0
        
        for program in programs:
            # Calculate the opening date
            calculated_date = program.calculate_program_opening_date()
            
            # Update if different
            if program.program_opening_date != calculated_date:
                program.program_opening_date = calculated_date
                program.save(update_fields=['program_opening_date'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated program "{program.title}" (ID: {program.program_id}) - Opening date: {calculated_date}'
                    )
                )
            else:
                self.stdout.write(
                    f'Program "{program.title}" (ID: {program.program_id}) - No update needed'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {programs.count()} programs. Updated {updated_count} programs.'
            )
        ) 