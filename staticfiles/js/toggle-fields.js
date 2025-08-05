// Toggle Fields JavaScript
// This file handles the checkbox functionality for activating search fields

document.addEventListener('DOMContentLoaded', function() {
    console.log('Toggle fields script loaded');
    
    // Function to toggle field visibility and enable/disable inputs
    function toggleField(toggleId, fieldId, isRange = false) {
        const toggle = document.getElementById(toggleId);
        const field = document.getElementById(fieldId);
        
        if (!toggle || !field) {
            console.log(`Toggle or field not found: ${toggleId}, ${fieldId}`);
            return;
        }
        
        if (toggle.checked) {
            field.style.display = 'block';
            // Enable all inputs within the field
            const inputs = field.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.removeAttribute('disabled');
            });
        } else {
            field.style.display = 'none';
            // Disable all inputs within the field
            const inputs = field.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.setAttribute('disabled', 'disabled');
                input.value = '';
            });
        }
    }
    
    // Function to handle range fields (min/max inputs)
    function toggleRangeField(toggleId, fieldId) {
        const toggle = document.getElementById(toggleId);
        const field = document.getElementById(fieldId);
        
        if (!toggle || !field) {
            console.log(`Toggle or field not found: ${toggleId}, ${fieldId}`);
            return;
        }
        
        if (toggle.checked) {
            field.style.display = 'block';
            // Enable min and max inputs
            const minInput = field.querySelector('input[id^="min_"]');
            const maxInput = field.querySelector('input[id^="max_"]');
            if (minInput) minInput.removeAttribute('disabled');
            if (maxInput) maxInput.removeAttribute('disabled');
        } else {
            field.style.display = 'none';
            // Disable and clear min and max inputs
            const minInput = field.querySelector('input[id^="min_"]');
            const maxInput = field.querySelector('input[id^="max_"]');
            if (minInput) {
                minInput.setAttribute('disabled', 'disabled');
                minInput.value = '';
            }
            if (maxInput) {
                maxInput.setAttribute('disabled', 'disabled');
                maxInput.value = '';
            }
        }
    }
    
    // Initialize all toggle switches
    function initializeToggles() {
        console.log('Initializing toggle switches...');
        
        // Define toggle mappings
        const toggleMappings = [
            // Query toggle
            { toggleId: 'query_toggle', fieldId: 'query_field' },
            
            // Project ID toggle
            { toggleId: 'project_id_toggle', fieldId: 'project_id_field' },
            
            // Project name toggle
            { toggleId: 'project_name_toggle', fieldId: 'project_name_field' },
            
            // Project types toggle
            { toggleId: 'project_types_toggle', fieldId: 'project_types_field' },
            
            // City toggle
            { toggleId: 'city_toggle', fieldId: 'city_field' },
            
            // Province toggle
            { toggleId: 'province_toggle', fieldId: 'province_field' },
            
            // Opening time filter toggle
            { toggleId: 'opening_time_filter_toggle', fieldId: 'opening_time_filter_field' },
            
            // Physical progress toggle (range)
            { toggleId: 'physical_progress_toggle', fieldId: 'physical_progress_field', isRange: true },
            
            // Financial progress toggle (range)
            { toggleId: 'financial_progress_toggle', fieldId: 'financial_progress_field', isRange: true },
            
            // Area size toggle (range)
            { toggleId: 'area_size_toggle', fieldId: 'area_size_field', isRange: true },
            
            // Notables toggle (range)
            { toggleId: 'notables_toggle', fieldId: 'notables_field', isRange: true },
            
            // Floor toggle (range)
            { toggleId: 'floor_toggle', fieldId: 'floor_field', isRange: true },
            
            // Project statuses toggle
            { toggleId: 'project_statuses_toggle', fieldId: 'project_statuses_field' },
            
            // Program ID toggle
            { toggleId: 'program_id_toggle', fieldId: 'program_id_field' },
            
            // Program title toggle
            { toggleId: 'program_title_toggle', fieldId: 'program_title_field' },
            
            // Program types toggle
            { toggleId: 'program_types_toggle', fieldId: 'program_types_field' },
            
            // License states toggle
            { toggleId: 'license_states_toggle', fieldId: 'license_states_field' },
            
            // Program province toggle
            { toggleId: 'program_province_toggle', fieldId: 'program_province_field' },
            
            // Cash allocation toggle (range)
            { toggleId: 'cash_allocation_toggle', fieldId: 'cash_allocation_fields', isRange: true },
            
            // Cash national toggle (range)
            { toggleId: 'cash_national_toggle', fieldId: 'cash_national_fields', isRange: true },
            
            // Cash province toggle (range)
            { toggleId: 'cash_province_toggle', fieldId: 'cash_province_fields', isRange: true },
            
            // Cash charity toggle (range)
            { toggleId: 'cash_charity_toggle', fieldId: 'cash_charity_fields', isRange: true },
            
            // Cash travel toggle (range)
            { toggleId: 'cash_travel_toggle', fieldId: 'cash_travel_fields', isRange: true },
            
            // Treasury allocation toggle (range)
            { toggleId: 'treasury_allocation_toggle', fieldId: 'treasury_allocation_fields', isRange: true },
            
            // Treasury national toggle (range)
            { toggleId: 'treasury_national_toggle', fieldId: 'treasury_national_fields', isRange: true },
            
            // Treasury province toggle (range)
            { toggleId: 'treasury_province_toggle', fieldId: 'treasury_province_fields', isRange: true },
            
            // Treasury travel toggle (range)
            { toggleId: 'treasury_travel_toggle', fieldId: 'treasury_travel_fields', isRange: true },
            
            // Total allocation toggle (range)
            { toggleId: 'total_allocation_toggle', fieldId: 'total_allocation_fields', isRange: true },
            
            // Required credit toggle (range)
            { toggleId: 'required_credit_toggle', fieldId: 'required_credit_fields', isRange: true },
            
            // Total debt toggle (range)
            { toggleId: 'total_debt_toggle', fieldId: 'total_debt_fields', isRange: true },
            
            // Required credit contracts toggle (range)
            { toggleId: 'required_credit_contracts_toggle', fieldId: 'required_credit_contracts_fields', isRange: true }
        ];
        
        // Set up event listeners for each toggle
        toggleMappings.forEach(mapping => {
            const toggle = document.getElementById(mapping.toggleId);
            if (toggle) {
                console.log(`Setting up toggle: ${mapping.toggleId}`);
                
                // Add event listener
                toggle.addEventListener('change', function() {
                    if (mapping.isRange) {
                        toggleRangeField(mapping.toggleId, mapping.fieldId);
                    } else {
                        toggleField(mapping.toggleId, mapping.fieldId);
                    }
                });
                
                // Initialize the field state based on current toggle state
                if (mapping.isRange) {
                    toggleRangeField(mapping.toggleId, mapping.fieldId);
                } else {
                    toggleField(mapping.toggleId, mapping.fieldId);
                }
            } else {
                console.log(`Toggle not found: ${mapping.toggleId}`);
            }
        });
    }
    
    // Initialize toggles when DOM is ready
    initializeToggles();
    
    // Also initialize when the page is fully loaded
    window.addEventListener('load', function() {
        console.log('Page fully loaded, re-initializing toggles...');
        initializeToggles();
    });
}); 