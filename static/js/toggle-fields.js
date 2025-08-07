// Toggle Functions for Search History Page

// Toggle query field
function toggleQueryField() {
    const toggle = document.getElementById('query_toggle');
    const field = document.getElementById('query');
    
    if (!toggle || !field) {
        console.log('Query toggle or field not found');
        return;
    }
    
    if (toggle.checked) {
        field.disabled = false;
    } else {
        field.disabled = true;
        field.value = '';
    }
}

// Generic toggle function for simple fields
function toggleField(toggle, fieldId) {
    const field = document.getElementById(fieldId);
    
    if (!toggle || !field) {
        console.log('Toggle or field not found:', fieldId);
        return;
    }
    
    field.disabled = !toggle.checked;
    if (!toggle.checked) {
        field.value = '';
    }
}

// Toggle project type field
function toggleProjectTypeField() {
    const toggle = document.getElementById('project_types_toggle');
    const container = document.getElementById('project_types_container');
    
    if (!toggle || !container) {
        console.log('Project type toggle or container not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
        // Uncheck all checkboxes
        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => checkbox.checked = false);
    }
}

// Toggle city field
function toggleCityField() {
    const toggle = document.getElementById('city_toggle');
    const container = document.getElementById('city_container');
    const field = document.getElementById('project_city');
    
    if (!toggle || !container || !field) {
        console.log('City toggle, container, or field not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
        field.disabled = false;
    } else {
        container.style.display = 'none';
        field.disabled = true;
        field.value = '';
    }
}

// Toggle province field
function toggleProvinceField() {
    const toggle = document.getElementById('province_toggle');
    const container = document.getElementById('province_container');
    
    if (!toggle || !container) {
        console.log('Province toggle or container not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
        // Uncheck all checkboxes
        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => checkbox.checked = false);
    }
}

// Toggle opening time filter
function handleOpeningTimeFilterToggle(toggle) {
    const field = document.getElementById('opening_time_date');
    
    if (!field) {
        console.log('Opening time date field not found');
        return;
    }
    
    if (toggle.checked) {
        field.disabled = false;
    } else {
        field.disabled = true;
        field.value = '';
    }
}

// Toggle physical progress field
function togglePhysicalProgressField() {
    const toggle = document.getElementById('physical_progress_toggle');
    const container = document.getElementById('physical_progress_container');
    const minInput = document.getElementById('min_physical_progress');
    const maxInput = document.getElementById('max_physical_progress');
    
    if (!toggle || !container || !minInput || !maxInput) {
        console.log('Physical progress elements not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        container.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

// Toggle financial progress field
function toggleFinancialProgressField() {
    const toggle = document.getElementById('financial_progress_toggle');
    const container = document.getElementById('financial_progress_container');
    const minInput = document.getElementById('min_financial_progress');
    const maxInput = document.getElementById('max_financial_progress');
    
    if (!toggle || !container || !minInput || !maxInput) {
        console.log('Financial progress elements not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        container.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

// Toggle area size field
function toggleAreaSizeField() {
    const toggle = document.getElementById('area_size_toggle');
    const container = document.getElementById('area_size_container');
    const minInput = document.getElementById('min_area_size');
    const maxInput = document.getElementById('max_area_size');
    
    if (!toggle || !container || !minInput || !maxInput) {
        console.log('Area size elements not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        container.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

// Toggle notables field
function toggleNotablesField() {
    const toggle = document.getElementById('notables_toggle');
    const container = document.getElementById('notables_container');
    const minInput = document.getElementById('min_notables');
    const maxInput = document.getElementById('max_notables');
    
    if (!toggle || !container || !minInput || !maxInput) {
        console.log('Notables elements not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        container.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

// Toggle floor field
function toggleFloorField() {
    const toggle = document.getElementById('floor_toggle');
    const container = document.getElementById('floor_container');
    const minInput = document.getElementById('min_floor');
    const maxInput = document.getElementById('max_floor');
    
    if (!toggle || !container || !minInput || !maxInput) {
        console.log('Floor elements not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        container.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

// Toggle site area field
function toggleSiteAreaField() {
    const toggle = document.getElementById('site_area_toggle');
    const container = document.getElementById('site_area_container');
    const minInput = document.getElementById('min_site_area');
    const maxInput = document.getElementById('max_site_area');
    
    console.log('toggleSiteAreaField called');
    console.log('toggle:', toggle);
    console.log('container:', container);
    console.log('minInput:', minInput);
    console.log('maxInput:', maxInput);
    
    if (!toggle || !container || !minInput || !maxInput) {
        console.log('Site area elements not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
        console.log('Site area fields enabled');
    } else {
        container.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
        console.log('Site area fields disabled');
    }
}

// Toggle wall length field
function toggleWallLengthField() {
    const toggle = document.getElementById('wall_length_toggle');
    const container = document.getElementById('wall_length_container');
    const minInput = document.getElementById('min_wall_length');
    const maxInput = document.getElementById('max_wall_length');
    
    console.log('toggleWallLengthField called');
    console.log('toggle:', toggle);
    console.log('container:', container);
    console.log('minInput:', minInput);
    console.log('maxInput:', maxInput);
    
    if (!toggle || !container || !minInput || !maxInput) {
        console.log('Wall length elements not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
        console.log('Wall length fields enabled');
    } else {
        container.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
        console.log('Wall length fields disabled');
    }
}

// Toggle project status field
function toggleProjectStatusField() {
    const toggle = document.getElementById('project_statuses_toggle');
    const container = document.getElementById('project_statuses_container');
    
    if (!toggle || !container) {
        console.log('Project status toggle or container not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
        // Uncheck all checkboxes
        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => checkbox.checked = false);
    }
}

// Toggle program type field
function toggleProgramTypeField() {
    const toggle = document.getElementById('program_types_toggle');
    const container = document.getElementById('program_types_container');
    
    if (!toggle || !container) {
        console.log('Program type toggle or container not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
        // Uncheck all checkboxes
        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => checkbox.checked = false);
    }
}

// Toggle license state field
function toggleLicenseStateField() {
    const toggle = document.getElementById('license_states_toggle');
    const container = document.getElementById('license_states_container');
    
    if (!toggle || !container) {
        console.log('License state toggle or container not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
        // Uncheck all checkboxes
        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => checkbox.checked = false);
    }
}

// Toggle program province field
function toggleProgramProvinceField() {
    const toggle = document.getElementById('program_province_toggle');
    const container = document.getElementById('program_province_container');
    
    if (!toggle || !container) {
        console.log('Program province toggle or container not found');
        return;
    }
    
    if (toggle.checked) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
        // Uncheck all checkboxes
        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => checkbox.checked = false);
    }
}

// Financial toggle functions
function toggleCashAllocationFields() {
    const toggle = document.getElementById('cash_allocation_toggle');
    const fields = document.getElementById('cash_allocation_fields');
    const minInput = document.getElementById('min_cash_allocation');
    const maxInput = document.getElementById('max_cash_allocation');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Cash allocation elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

function toggleCashNationalFields() {
    const toggle = document.getElementById('cash_national_toggle');
    const fields = document.getElementById('cash_national_fields');
    const minInput = document.getElementById('min_cash_national');
    const maxInput = document.getElementById('max_cash_national');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Cash national elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

function toggleCashProvinceFields() {
    const toggle = document.getElementById('cash_province_toggle');
    const fields = document.getElementById('cash_province_fields');
    const minInput = document.getElementById('min_cash_province');
    const maxInput = document.getElementById('max_cash_province');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Cash province elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

function toggleCashCharityFields() {
    const toggle = document.getElementById('cash_charity_toggle');
    const fields = document.getElementById('cash_charity_fields');
    const minInput = document.getElementById('min_cash_charity');
    const maxInput = document.getElementById('max_cash_charity');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Cash charity elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

function toggleCashTravelFields() {
    const toggle = document.getElementById('cash_travel_toggle');
    const fields = document.getElementById('cash_travel_fields');
    const minInput = document.getElementById('min_cash_travel');
    const maxInput = document.getElementById('max_cash_travel');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Cash travel elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

function toggleTreasuryAllocationFields() {
    const toggle = document.getElementById('treasury_allocation_toggle');
    const fields = document.getElementById('treasury_allocation_fields');
    const minInput = document.getElementById('min_treasury_allocation');
    const maxInput = document.getElementById('max_treasury_allocation');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Treasury allocation elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

function toggleTreasuryNationalFields() {
    const toggle = document.getElementById('treasury_national_toggle');
    const fields = document.getElementById('treasury_national_fields');
    const minInput = document.getElementById('min_treasury_national');
    const maxInput = document.getElementById('max_treasury_national');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Treasury national elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

function toggleTreasuryProvinceFields() {
    const toggle = document.getElementById('treasury_province_toggle');
    const fields = document.getElementById('treasury_province_fields');
    const minInput = document.getElementById('min_treasury_province');
    const maxInput = document.getElementById('max_treasury_province');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Treasury province elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

function toggleTreasuryTravelFields() {
    const toggle = document.getElementById('treasury_travel_toggle');
    const fields = document.getElementById('treasury_travel_fields');
    const minInput = document.getElementById('min_treasury_travel');
    const maxInput = document.getElementById('max_treasury_travel');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Treasury travel elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

function toggleTotalAllocationFields() {
    const toggle = document.getElementById('total_allocation_toggle');
    const fields = document.getElementById('total_allocation_fields');
    const minInput = document.getElementById('min_total_allocation');
    const maxInput = document.getElementById('max_total_allocation');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Total allocation elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

function toggleRequiredCreditFields() {
    const toggle = document.getElementById('required_credit_toggle');
    const fields = document.getElementById('required_credit_fields');
    const minInput = document.getElementById('min_required_credit');
    const maxInput = document.getElementById('max_required_credit');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Required credit elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

function toggleTotalDebtFields() {
    const toggle = document.getElementById('total_debt_toggle');
    const fields = document.getElementById('total_debt_fields');
    const minDebt = document.getElementById('min_total_debt');
    const maxDebt = document.getElementById('max_total_debt');
    
    if (!toggle || !fields || !minDebt || !maxDebt) {
        console.log('Total debt elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minDebt.disabled = false;
        maxDebt.disabled = false;
    } else {
        fields.style.display = 'none';
        minDebt.disabled = true;
        maxDebt.disabled = true;
        minDebt.value = '';
        maxDebt.value = '';
    }
}

function toggleRequiredCreditContractsFields() {
    const toggle = document.getElementById('required_credit_contracts_toggle');
    const fields = document.getElementById('required_credit_contracts_fields');
    const minInput = document.getElementById('min_required_credit_contracts');
    const maxInput = document.getElementById('max_required_credit_contracts');
    
    if (!toggle || !fields || !minInput || !maxInput) {
        console.log('Required credit contracts elements not found');
        return;
    }
    
    if (toggle.checked) {
        fields.style.display = 'block';
        minInput.disabled = false;
        maxInput.disabled = false;
    } else {
        fields.style.display = 'none';
        minInput.disabled = true;
        maxInput.disabled = true;
        minInput.value = '';
        maxInput.value = '';
    }
}

// Initialize all toggle functions when document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded - Initializing toggle functions');
    
    // Initialize all toggle functions
    toggleQueryField();
    toggleProjectTypeField();
    toggleCityField();
    toggleProvinceField();
    togglePhysicalProgressField();
    toggleFinancialProgressField();
    toggleAreaSizeField();
    toggleNotablesField();
    toggleFloorField();
    toggleSiteAreaField();
    toggleWallLengthField();
    toggleProjectStatusField();
    toggleProgramTypeField();
    toggleLicenseStateField();
    toggleProgramProvinceField();
    toggleCashAllocationFields();
    toggleCashNationalFields();
    toggleCashProvinceFields();
    toggleCashCharityFields();
    toggleCashTravelFields();
    toggleTreasuryAllocationFields();
    toggleTreasuryNationalFields();
    toggleTreasuryProvinceFields();
    toggleTreasuryTravelFields();
    toggleTotalAllocationFields();
    toggleRequiredCreditFields();
    toggleTotalDebtFields();
    toggleRequiredCreditContractsFields();
    
    // Initialize opening time filter
    const openingTimeFilterToggle = document.getElementById('opening_time_filter_toggle');
    if (openingTimeFilterToggle) {
        handleOpeningTimeFilterToggle(openingTimeFilterToggle);
    }
    
    // Test the new toggle functions
    console.log('Testing site area toggle function...');
    const siteAreaToggle = document.getElementById('site_area_toggle');
    if (siteAreaToggle) {
        console.log('✓ Site area toggle found');
        siteAreaToggle.addEventListener('change', function() {
            console.log('Site area toggle changed:', this.checked);
            toggleSiteAreaField();
        });
    } else {
        console.log('✗ Site area toggle not found');
    }
    
    console.log('Testing wall length toggle function...');
    const wallLengthToggle = document.getElementById('wall_length_toggle');
    if (wallLengthToggle) {
        console.log('✓ Wall length toggle found');
        wallLengthToggle.addEventListener('change', function() {
            console.log('Wall length toggle changed:', this.checked);
            toggleWallLengthField();
        });
    } else {
        console.log('✗ Wall length toggle not found');
    }
});

// Add global test functions for debugging
window.testSiteAreaToggle = function() {
    console.log('Testing site area toggle manually...');
    toggleSiteAreaField();
};

window.testWallLengthToggle = function() {
    console.log('Testing wall length toggle manually...');
    toggleWallLengthField();
};