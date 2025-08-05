/**
 * Direct fix for the money input field reset issue and ریال text
 * Applies immediately on page load to ensure no currency symbols are shown in inputs
 * Ensures proper comma formatting for currency inputs
 */

(function() {
    // Function to add commas to numbers
    function addCommas(num) {
        if (!num && num !== 0) return '';
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
    
    // Function to remove non-digit characters except commas
    function cleanNumber(value) {
        return value.replace(/[^\d,]/g, '');
    }
    
    // Function to get only digits
    function getDigitsOnly(value) {
        return value.replace(/[^\d]/g, '');
    }
    
    // Function to setup proper currency input formatting
    function setupCurrencyInput(input) {
        // Exclude contractor_name field completely
        if (input.name === 'contractor_name' || input.id === 'contractor_name' || 
            input.name === 'contractor_id' || input.id === 'contractor_id' ||
            input.classList.contains('text-field-only') ||
            input.getAttribute('data-exclude-currency') === 'true') {
            console.log('Excluding field from currency formatting:', input.name || input.id);
            return;
        }
        
        console.log('Setting up currency input:', input.name || input.id);
        
        // Remove any ریال text and format existing value
        if (input.value) {
            const digitsOnly = getDigitsOnly(input.value);
            if (digitsOnly) {
                input.value = addCommas(digitsOnly);
                console.log('Initial formatting applied:', input.value);
            }
        }
        
        // Apply CSS to prevent pseudo-elements
        input.style.setProperty('padding-left', '1rem', 'important');
        input.style.setProperty('padding-right', '1rem', 'important');
        
        // Add class for identification
        input.classList.add('currency-input-fixed');
        
        // Add placeholder
        input.placeholder = 'مقدار به ریال';
        
        // Input event for real-time formatting
        input.addEventListener('input', function(e) {
            const cursorPos = this.selectionStart || 0;
            const oldValue = this.value;
            
            // Remove ریال text if present
            if (this.value.includes('ریال')) {
                this.value = this.value.replace(/ریال/g, '').trim();
            }
            
            // Get digits only
            const digitsOnly = getDigitsOnly(this.value);
            
            // Allow empty input
            if (this.value === '' || digitsOnly === '') {
                return;
            }
            
            // Format with commas
            const formatted = addCommas(digitsOnly);
            
            // Only update if value actually changed
            if (this.value !== formatted) {
                this.value = formatted;
                
                // Calculate proper cursor position
                // Count digits before cursor in old value
                const digitsBefore = oldValue.substring(0, cursorPos).replace(/[^\d]/g, '').length;
                
                // Find position after formatting
                let newCursorPos = 0;
                let digitCount = 0;
                
                for (let i = 0; i < formatted.length; i++) {
                    if (formatted[i].match(/\d/)) {
                        digitCount++;
                        if (digitCount === digitsBefore) {
                            newCursorPos = i + 1;
                            break;
                        }
                    }
                }
                
                // If we're at the end, place cursor at the end
                if (digitCount < digitsBefore || digitsBefore === 0) {
                    newCursorPos = formatted.length;
                }
                
                // Set cursor position
                setTimeout(() => {
                    try {
                        this.setSelectionRange(newCursorPos, newCursorPos);
                    } catch (e) {
                        // Ignore cursor position errors
                    }
                }, 0);
            }
        });
        
        // Keydown event to restrict input to numbers only
        input.addEventListener('keydown', function(e) {
            // Allow: backspace, delete, tab, escape, enter, home, end, left, right, up, down
            const allowedKeys = [8, 9, 27, 13, 46, 35, 36, 37, 38, 39, 40];
            
            if (allowedKeys.indexOf(e.keyCode) !== -1 ||
                // Allow Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
                (e.ctrlKey && [65, 67, 86, 88].indexOf(e.keyCode) !== -1)) {
                return;
            }
            
            // Ensure that it is a number
            if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
                e.preventDefault();
            }
        });
        
        // Focus event
        input.addEventListener('focus', function() {
            if (this.value === '0') {
                this.value = '';
            }
            // Remove ریال if present
            if (this.value.includes('ریال')) {
                this.value = this.value.replace(/ریال/g, '').trim();
            }
        });
        
        // Blur event
        input.addEventListener('blur', function() {
            // Remove ریال if present
            if (this.value.includes('ریال')) {
                this.value = this.value.replace(/ریال/g, '').trim();
            }
            
            // Ensure proper formatting
            const digitsOnly = getDigitsOnly(this.value);
            if (digitsOnly) {
                this.value = addCommas(digitsOnly);
            }
        });
        
        // Paste event
        input.addEventListener('paste', function(e) {
            setTimeout(() => {
                const digitsOnly = getDigitsOnly(this.value);
                if (digitsOnly) {
                    this.value = addCommas(digitsOnly);
                }
            }, 0);
        });
    }
    
    // Function to run immediately
    function fixMoneyInputs() {
        console.log('Currency input fix running...');
        
        // Find all money-related input fields
        const moneyInputs = document.querySelectorAll(
            'input[name*="amount"], input[name*="price"], ' +
            'input[name*="cost"], input[name*="budget"], ' +
            'input[name*="payment"], input[name*="fee"], ' +
            'input[id*="amount"], input[id*="price"], ' +
            'input[id*="cost"], input[id*="budget"], ' +
            'input[id*="payment"], input[id*="fee"], ' +
            'input[id*="contract"]'
        );
        
        console.log('Found money inputs:', moneyInputs.length);
        
        // Setup each money input
        moneyInputs.forEach(function(input) {
            if (!input.classList.contains('currency-input-fixed')) {
                setupCurrencyInput(input);
            }
        });
        
        // Specifically target the contract amount field مبلغ قرارداد
        const contractLabels = Array.from(document.querySelectorAll('label')).filter(
            label => label.textContent && label.textContent.includes('مبلغ قرارداد')
        );
        
        console.log('Found contract labels:', contractLabels.length);
        
        contractLabels.forEach(function(label) {
            const fieldId = label.getAttribute('for');
            if (fieldId) {
                const field = document.getElementById(fieldId);
                if (field && !field.classList.contains('currency-input-fixed')) {
                    console.log('Processing contract field:', fieldId, 'value:', field.value);
                    
                    // Create a style element to override any existing styles
                    const style = document.createElement('style');
                    style.textContent = `
                        #${fieldId}::before, #${fieldId}::after {
                            content: none !important;
                            display: none !important;
                        }
                        #${fieldId} {
                            padding-left: 1rem !important;
                            padding-right: 1rem !important;
                        }
                    `;
                    document.head.appendChild(style);
                    
                    setupCurrencyInput(field);
                }
            }
        });
        
        // Also fix any inputs with value containing ریال
        const allInputs = document.querySelectorAll('input[type="text"], input[type="number"]');
        allInputs.forEach(function(input) {
            // ---- START ADDED EXCLUSION ----
            if (input.name === 'contractor_name' || input.id === 'contractor_name' ||
                input.name === 'contractor_id' || input.id === 'contractor_id' ||
                input.classList.contains('text-field-only') ||
                input.getAttribute('data-exclude-currency') === 'true') {
                console.log('[currency-input-fix] allInputs loop: Excluding field:', input.name || input.id);
                // Ensure its placeholder is correct and it's not styled like currency
                if (input.name === 'contractor_name' || input.id === 'contractor_name') {
                    if (input.placeholder !== 'نام پیمانکار') {
                        input.placeholder = 'نام پیمانکار';
                    }
                } else if (input.name === 'contractor_id' || input.id === 'contractor_id') {
                    if (input.placeholder !== 'شناسه پیمانکار') {
                        input.placeholder = 'شناسه پیمانکار';
                    }
                }
                input.style.textAlign = 'right'; // Or 'left' as appropriate for Persian text
                input.classList.remove('currency-input', 'currency-input-enhanced', 'currency-input-fixed');
                // Attempt to remove listeners if possible, though this is hard to do generically
                return; // Skip further processing for this excluded field
            }
            // ---- END ADDED EXCLUSION ----

            if (input.value && input.value.includes('ریال')) {
                const digitsOnly = getDigitsOnly(input.value);
                if (digitsOnly) {
                    input.value = addCommas(digitsOnly);
                    console.log('General input formatted:', input.value);
                }
                
                // Add event listener to prevent ریال from reappearing
                if (!input.classList.contains('currency-input-fixed')) {
                    input.addEventListener('input', function() {
                        if (this.value && this.value.includes('ریال')) {
                            const digits = getDigitsOnly(this.value);
                            this.value = digits ? addCommas(digits) : '';
                        }
                    });
                }
            }
        });
        
        console.log('Currency input fix completed');
    }
    
    // Run immediately
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixMoneyInputs);
    } else {
        fixMoneyInputs();
    }
    
    // Also run after delays to catch any late-loaded fields
    setTimeout(fixMoneyInputs, 500);
    setTimeout(fixMoneyInputs, 1000);
    setTimeout(fixMoneyInputs, 2000);
})(); 