from django.core.management.base import BaseCommand
from creator_program.models import Program
import random

class Command(BaseCommand):
    help = 'Add sample coordinates to projects for map testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of projects to add coordinates to',
        )

    def handle(self, *args, **options):
        # Sample coordinates for different Iranian provinces
        province_coordinates = {
            'تهران': [(51.389, 35.689), (51.422, 35.751), (51.364, 35.699)],
            'اصفهان': [(51.677, 32.657), (51.655, 32.640), (51.696, 32.674)],
            'شیراز': [(52.588, 29.591), (52.563, 29.610), (52.605, 29.575)],
            'مازندران': [(52.012, 36.566), (52.033, 36.548), (51.989, 36.583)],
            'خراسان رضوی': [(59.104, 36.315), (59.084, 36.297), (59.125, 36.334)],
            'گیلان': [(50.006, 37.279), (49.987, 37.261), (50.025, 37.296)],
            'آذربایجان شرقی': [(46.292, 38.080), (46.273, 38.062), (46.311, 38.098)],
            'خوزستان': [(48.684, 31.319), (48.665, 31.301), (48.703, 31.337)],
            'فارس': [(52.588, 29.591), (52.563, 29.610), (52.605, 29.575)],
        }
        
        # Get programs without coordinates
        programs_without_coords = Program.objects.filter(
            longitude__isnull=True, 
            latitude__isnull=True
        )
        
        if not programs_without_coords.exists():
            self.stdout.write(
                self.style.WARNING('No programs without coordinates found.')
            )
            return
        
        count = min(options['count'], programs_without_coords.count())
        programs_to_update = programs_without_coords[:count]
        
        updated_count = 0
        for program in programs_to_update:
            # Try to find coordinates for the program's province
            coords_list = None
            for province, coords in province_coordinates.items():
                if province in program.province:
                    coords_list = coords
                    break
            
            # If no specific coordinates for province, use Tehran as default
            if not coords_list:
                coords_list = province_coordinates['تهران']
            
            # Pick random coordinates from the list
            lng, lat = random.choice(coords_list)
            
            # Add some random variation
            lng += random.uniform(-0.01, 0.01)
            lat += random.uniform(-0.01, 0.01)
            
            program.longitude = lng
            program.latitude = lat
            program.save()
            
            updated_count += 1
            self.stdout.write(
                f'Updated program "{program.title}" with coordinates ({lng:.6f}, {lat:.6f})'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} programs with coordinates.')
        ) 