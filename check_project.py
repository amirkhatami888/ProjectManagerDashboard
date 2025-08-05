import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')
django.setup()

# Import models after setting up Django
from creator_project.models import Project

# Get project by ID
project_id = 34
p = Project.objects.get(id=project_id)
print(f'Project ID: {p.id}, Name: {p.name}')
print(f'Physical Progress from Django: {p.calculate_physical_progress()}%')

# Calculate manually
subprojects = p.subprojects.all().order_by('id')
total_weight = 0
weighted_progress = 0

print('\nSubprojects details:')
for i, s in enumerate(subprojects, 1):
    weight = s.final_contract_amount
    progress = s.physical_progress or 0
    
    if s.contract_amount is not None:
        weight_source = f"contract_amount={s.contract_amount}"
        if s.has_adjustment == 'دارد' and s.adjustment_coefficient is not None:
            weight_source += f" × adjustment_coefficient={s.adjustment_coefficient}"
    else:
        weight_source = f"imagenrary_cost={s.imagenrary_cost}"
    
    print(f'Subproject #{i} (ID: {s.id}, Number: {s.sub_project_number}): Type={s.sub_project_type}, Progress={progress}%, Weight={weight} ({weight_source})')
    
    if weight is not None:
        weight = float(weight)
        progress = float(progress)
        contribution = weight * progress
        
        print(f'  Contribution: {weight} × {progress}% = {contribution}')
        
        total_weight += weight
        weighted_progress += contribution

print(f'\nTotal weight sum: {total_weight}')
print(f'Weighted progress sum: {weighted_progress}')

if total_weight > 0:
    result = weighted_progress / total_weight
    print(f'Manual calculation: {weighted_progress} ÷ {total_weight} = {result}%')
    print(f'Rounded to 2 decimals: {round(result, 2)}%')
else:
    print('Cannot calculate: total weight is zero')

print(f'Expected value from user: 4.975135605651512%')

# Detailed calculation for verification
print("\nDetailed calculation for verification:")
print(f"(0 × 1234.00 + 10 × 123456.00 + 0 × 123456.00) ÷ (1234.00 + 123456.00 + 123456.00)")
print(f"(0 + 1234560.00 + 0) ÷ 248146.00")
print(f"1234560.00 ÷ 248146.00 = {1234560.00 / 248146.00}%")
print(f"Rounded to 2 decimals: {round(1234560.00 / 248146.00, 2)}%") 