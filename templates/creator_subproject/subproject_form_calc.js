// Handle relationship type based on selected related_subproject
document.getElementById('related_subproject').addEventListener('change', function() {
    var relatedSubproject = this.value;
    var relationshipType = document.getElementById('relationship_type');
    var relationshipDelay = document.getElementById('relationship_delay');
    var relationshipTypeDiv = relationshipType.closest('.col-md-4');
    var relationshipDelayDiv = relationshipDelay.closest('.col-md-4');
    
    if (relatedSubproject === 'floating') {
        // If floating is selected, hide both relationship type and delay fields
        relationshipTypeDiv.style.display = 'none';
        relationshipDelayDiv.style.display = 'none';
        relationshipType.value = 'شناور';
    } else if (relatedSubproject === '') {
        // If no relationship is selected, hide both fields
        relationshipTypeDiv.style.display = 'none';
        relationshipDelayDiv.style.display = 'none';
        relationshipType.value = '';
    } else {
        // Otherwise, show both fields
        relationshipTypeDiv.style.display = 'block';
        relationshipDelayDiv.style.display = 'block';
        
        // If previously was floating, clear the selection
        if (relationshipType.value === 'شناور') {
            relationshipType.value = '';
        }
    }
});

// Initialize the relationship controls on page load
function initializeRelationshipControls() {
    var relatedSubproject = document.getElementById('related_subproject').value;
    var relationshipType = document.getElementById('relationship_type');
    var relationshipDelay = document.getElementById('relationship_delay');
    var relationshipTypeDiv = relationshipType.closest('.col-md-4');
    var relationshipDelayDiv = relationshipDelay.closest('.col-md-4');
    
    if (relatedSubproject === 'floating') {
        // Hide both fields and set relationship type to شناور
        relationshipTypeDiv.style.display = 'none';
        relationshipDelayDiv.style.display = 'none';
        relationshipType.value = 'شناور';
    } else if (relatedSubproject === '') {
        // If no relationship is selected, hide both fields
        relationshipTypeDiv.style.display = 'none';
        relationshipDelayDiv.style.display = 'none';
    } else {
        // Show both fields
        relationshipTypeDiv.style.display = 'block';
        relationshipDelayDiv.style.display = 'block';
    }
}

// Calculate the final contract amount
function calculateFinalAmount() {
    var contract_amount = document.getElementById('contract_amount').value;
    var has_adjustment = document.getElementById('has_adjustment').value;
    var adjustment_percentage = 0;
    
    if (has_adjustment === 'دارد') {
        adjustment_percentage = document.getElementById('adjustment_coefficient').value;
        
        // Convert percentage to decimal (e.g., 25% becomes 0.25)
        adjustment_percentage = parseFloat(adjustment_percentage) || 0;
        adjustment_coefficient = adjustment_percentage / 100;
    } else {
        adjustment_coefficient = 0;
    }
    
    // Calculate final amount (contract amount × (1 + coefficient))
    var final_amount = contract_amount * (1 + adjustment_coefficient);
    document.getElementById('final_contract_amount').value = final_amount;
} 