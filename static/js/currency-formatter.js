/**
 * Enhanced Currency formatter using autoNumeric.js library
 * Provides robust currency formatting for Rial with left-positioned symbol
 * Fixes three-digit reset issue and maintains cursor position
 */

// AutoNumeric configuration for Rial currency - no symbol since CSS handles it
const rialConfig = {
    currencySymbol: '', // Empty - CSS handles it
    currencySymbolPlacement: 'p',
    digitGroupSeparator: ',',
    decimalCharacter: '.',
    decimalPlaces: 0,
    allowDecimalPadding: false,
    minimumValue: '0',
    maximumValue: '999999999999999',
    emptyInputBehavior: 'focus',
    formatOnPageLoad: true,
    selectNumberOnly: true,
    unformatOnSubmit: false,
    showWarnings: false,
    modifyValueOnWheel: false,
    watchExternalChanges: true,
    styleRules: {
        positive: 'autoNumeric-positive',
        negative: 'autoNumeric-negative'
    }
};

// Initialize autoNumeric instances storage
const autoNumericInstances = new Map();

// Load autoNumeric library dynamically
function loadAutoNumeric() {
    return new Promise((resolve, reject) => {
        if (window.AutoNumeric) {
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/autonumeric/4.10.8/autoNumeric.min.js';
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load autoNumeric library'));
        document.head.appendChild(script);
    });
}

// Enhanced currency field setup with autoNumeric
async function setupEnhancedCurrencyField(element) {
    try {
        await loadAutoNumeric();
        
        if (!element || autoNumericInstances.has(element)) {
            return;
        }


        // Remove any existing ریال text
        if (element.value && element.value.includes('ریال')) {
            element.value = element.value.replace(/ریال/g, '').trim();
        }

        // Create autoNumeric instance
        const anElement = new AutoNumeric(element, rialConfig);
        autoNumericInstances.set(element, anElement);

        // Add custom styling
        element.classList.add('currency-input-enhanced');
        
        // Handle form submission
        if (element.form) {
            element.form.addEventListener('submit', function() {
                // Get the raw numeric value for form submission
                const rawValue = anElement.getNumber();
                
                // Create or update hidden input with raw value
                const hiddenId = element.id + '_raw';
                let hiddenInput = document.getElementById(hiddenId);
                
                if (!hiddenInput) {
                    hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.id = hiddenId;
                    hiddenInput.name = element.name;
                    element.parentNode.appendChild(hiddenInput);
                }
                
                hiddenInput.value = rawValue || '0';
            });
        }

        // Handle focus events for better UX
        element.addEventListener('focus', function() {
            this.classList.add('currency-input-focused');
            
            // Ensure no ریال text on focus
            if (this.value && this.value.includes('ریال')) {
                const cleanValue = this.value.replace(/ریال/g, '').trim();
                anElement.set(cleanValue, {
                    keepFocus: true
                });
            }
        });

        element.addEventListener('blur', function() {
            this.classList.remove('currency-input-focused');
        });

        // Handle input to ensure no ریال is added
        element.addEventListener('input', function(e) {
            if (this.value && this.value.includes('ریال')) {
                const cleanValue = this.value.replace(/ریال/g, '').trim();
                anElement.set(cleanValue, {
                    keepFocus: true
                });
            }
        });

        return anElement;
    } catch (error) {
        console.error('Failed to setup enhanced currency field:', error);
        // Fallback to basic formatting if autoNumeric fails
        setupBasicCurrencyField(element);
    }
}

// Fallback basic currency formatting - no ریال symbol
function setupBasicCurrencyField(element) {
    if (!element) return;

    // Add placeholder to indicate currency
    element.placeholder = 'مقدار به ریال';
    
    // Remove any existing ریال text
    if (element.value && element.value.includes('ریال')) {
        element.value = element.value.replace(/ریال/g, '').trim();
    }
    
    // Store the current value to prevent resets
    let isProcessing = false;

    function formatWithCommas(number) {
        if (!number && number !== 0) return '';
        // Convert to string and add commas every 3 digits from right
        return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    function parseNumber(value) {
        // Remove all non-digit characters
        return value.replace(/[^\d]/g, '');
    }

    element.addEventListener('input', function(e) {
        if (isProcessing) return;
        
        isProcessing = true;
        
        const currentCursorPos = this.selectionStart || 0;
        const currentValue = this.value;
        
        // Handle empty input
        if (currentValue === '') {
            isProcessing = false;
            return;
        }
        
        // Remove ریال if present
        if (currentValue.includes('ریال')) {
            this.value = currentValue.replace(/ریال/g, '').trim();
        }
        
        // Get digits only
        const digitsOnly = parseNumber(this.value);
        
        // If no digits, allow empty
        if (!digitsOnly) {
            if (this.value !== '') {
                this.value = '';
            }
            isProcessing = false;
            return;
        }
        
        // Format with commas
        const formatted = formatWithCommas(digitsOnly);
        
        // Only update if value changed
        if (this.value !== formatted) {
            this.value = formatted;
            
            // Calculate cursor position based on digit count
            const digitsBefore = currentValue.substring(0, currentCursorPos).replace(/[^\d]/g, '').length;
            let newCursorPos = 0;
            let digitCount = 0;
            
            for (let i = 0; i < formatted.length; i++) {
                if (formatted[i].match(/\d/)) {
                    digitCount++;
                    if (digitCount === digitsBefore) {
                        newCursorPos = i + 1;
                        break;
                    }
                } else if (digitCount < digitsBefore) {
                    newCursorPos = i + 1;
                }
            }
            
            // If at end or beyond, place at end
            if (digitCount < digitsBefore) {
                newCursorPos = formatted.length;
            }
            
            // Set cursor position
            setTimeout(() => {
                try {
                    this.setSelectionRange(newCursorPos, newCursorPos);
                } catch (e) {
                    console.warn('Could not set cursor position:', e);
                }
                isProcessing = false;
            }, 0);
        } else {
            isProcessing = false;
        }
    });

    element.addEventListener('keydown', function(e) {
        // Allow: backspace, delete, tab, escape, enter
        if ([8, 9, 27, 13, 46].indexOf(e.keyCode) !== -1 ||
            // Allow: Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
            (e.keyCode === 65 && e.ctrlKey === true) ||
            (e.keyCode === 67 && e.ctrlKey === true) ||
            (e.keyCode === 86 && e.ctrlKey === true) ||
            (e.keyCode === 88 && e.ctrlKey === true) ||
            // Allow: home, end, left, right, down, up
            (e.keyCode >= 35 && e.keyCode <= 40)) {
            return;
        }
        // Ensure that it is a number and stop the keypress
        if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
            e.preventDefault();
        }
    });

    element.addEventListener('paste', function(e) {
        // Handle paste events
        setTimeout(() => {
            const pastedValue = this.value;
            const digitsOnly = parseNumber(pastedValue);
            const formatted = formatWithCommas(digitsOnly);
            
            if (this.value !== formatted) {
                this.value = formatted;
                // Set cursor to end after paste
                setTimeout(() => {
                    this.setSelectionRange(formatted.length, formatted.length);
                }, 0);
            }
        }, 0);
    });

    element.addEventListener('blur', function() {
        // Remove any ریال that might have been added
        if (this.value.includes('ریال')) {
            this.value = this.value.replace(/ریال/g, '').trim();
        }
        
        // Ensure proper formatting on blur
        const digitsOnly = parseNumber(this.value);
        if (digitsOnly) {
            const formatted = formatWithCommas(digitsOnly);
            this.value = formatted;
        }
    });

    element.addEventListener('focus', function() {
        // Clear zero values
        if (this.value === '0') {
            this.value = '';
        }
        
        // Remove any ریال that might have been added
        if (this.value.includes('ریال')) {
            this.value = this.value.replace(/ریال/g, '').trim();
        }
    });

    // Initial formatting if there's already a value
    if (element.value) {
        const digitsOnly = parseNumber(element.value);
        if (digitsOnly) {
            const formatted = formatWithCommas(digitsOnly);
            element.value = formatted;
        }
    }
}

// Setup currency container with enhanced styling
function setupEnhancedCurrencyContainer() {
    document.querySelectorAll('.currency-input').forEach(async input => {
        // Skip if already processed
        if (input.classList.contains('currency-input-enhanced') || 
            input.closest('.currency-input-container-enhanced')) {
            return;
        }

        // Remove any ریال text from the input
        if (input.value && input.value.includes('ریال')) {
            input.value = input.value.replace(/ریال/g, '').trim();
        }

        // Create enhanced container
        const container = document.createElement('div');
        container.className = 'currency-input-container-enhanced';
        
        // Add a separate label for currency
        const currencyLabel = document.createElement('span');
        currencyLabel.className = 'currency-label';
        currencyLabel.textContent = 'ریال';
        
        // Insert container before input
        input.parentNode.insertBefore(container, input);
        
        // Move input into container
        container.appendChild(input);
        container.appendChild(currencyLabel);
        
        // Setup enhanced currency field
        await setupEnhancedCurrencyField(input);
    });
}

// Auto-detect and enhance currency fields
async function autoDetectCurrencyFields() {
    const potentialFields = document.querySelectorAll('input[type="number"], input[type="text"]');
    
    for (const input of potentialFields) {
        // Skip if already processed
        if (input.classList.contains('currency-input') || 
            input.classList.contains('currency-input-enhanced')) {
            continue;
        }
        
        // Skip if marked to exclude from currency formatting
        if (input.getAttribute('data-exclude-currency') === 'true' ||
            input.classList.contains('date-field-only') ||
            input.classList.contains('text-field-only') ||
            input.classList.contains('date-input') ||
            input.name === 'allocation_date_display' ||
            input.name === 'contractor_name' ||
            input.id === 'id_allocation_date_display' ||
            input.name && input.name.includes('date') ||
            input.id && input.id.includes('date')) {
            continue;
        }

        // Check if field is currency-related
        const label = input.previousElementSibling || 
                     document.querySelector(`label[for="${input.id}"]`);
        
        if (label && label.textContent && 
            (label.textContent.includes('ریال') || 
             label.textContent.includes('مبلغ') ||
             label.textContent.includes('پرداختی') ||
             label.textContent.includes('تخصیص')) &&
            !label.textContent.includes('تاریخ')) { // Exclude date fields
            
            // Remove any ریال text from the input
            if (input.value && input.value.includes('ریال')) {
                input.value = input.value.replace(/ریال/g, '').trim();
            }
            
            input.classList.add('currency-input');
            
            // Create enhanced container
            const container = document.createElement('div');
            container.className = 'currency-input-container-enhanced';
            
            // Add separate label for currency
            const currencyLabel = document.createElement('span');
            currencyLabel.className = 'currency-label';
            currencyLabel.textContent = 'ریال';
            
            input.parentNode.insertBefore(container, input);
            container.appendChild(input);
            container.appendChild(currencyLabel);
            
            await setupEnhancedCurrencyField(input);
        }
    }
}

// Format read-only currency displays - no duplicate symbols
function formatReadOnlyCurrencyDisplays() {
    document.querySelectorAll('.currency-display, .currency-amount').forEach(element => {
        if (element.dataset.formatted) return;
        
        const text = element.textContent.trim();
        // Remove any ریال from the text first
        const cleanText = text.replace(/ریال/g, '').trim();
        const numericValue = cleanText.replace(/[^\d]/g, '');
        
        if (numericValue) {
            const formatted = numericValue.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            // Only set the numeric value, CSS pseudo-element handles ریال symbol
            element.textContent = formatted;
            element.dataset.formatted = 'true';
        }
    });
}

// Process all money-related fields on page
function processMoneyCurrencyFields() {
    // Find all money/amount related fields by name or ID pattern
    const moneyFields = document.querySelectorAll(
        'input[name*="amount"], input[name*="price"], ' +
        'input[name*="cost"], input[name*="budget"], ' +
        'input[name*="payment"], input[name*="fee"], ' +
        'input[id*="amount"], input[id*="price"], ' +
        'input[id*="cost"], input[id*="budget"], ' +
        'input[id*="payment"], input[id*="fee"]'
    );
    
    moneyFields.forEach(field => {
        // Skip if already processed
        if (field.classList.contains('currency-input') || 
            field.classList.contains('currency-input-enhanced')) {
            return;
        }
        
        // Skip if marked to exclude from currency formatting
        if (field.getAttribute('data-exclude-currency') === 'true' ||
            field.classList.contains('date-field-only') ||
            field.classList.contains('text-field-only') ||
            field.classList.contains('date-input') ||
            field.name === 'allocation_date_display' ||
            field.name === 'contractor_name' || field.name === 'contractor_id' ||
            field.id === 'id_allocation_date_display' ||
            field.name && field.name.includes('date') ||
            field.id && field.id.includes('date')) {
            return;
        }
        
        // Remove any ریال text
        if (field.value && field.value.includes('ریال')) {
            field.value = field.value.replace(/ریال/g, '').trim();
        }
        
        field.classList.add('currency-input');
        setupBasicCurrencyField(field);
    });
}

// Direct fix for contract amount field
function fixContractAmountField() {
    // Find the contract amount field "مبلغ قرارداد"
    const contractAmountField = Array.from(document.querySelectorAll('label')).find(
        label => label.textContent && label.textContent.includes('مبلغ قرارداد')
    );
    
    if (contractAmountField) {
        const fieldId = contractAmountField.getAttribute('for');
        if (fieldId) {
            const inputField = document.getElementById(fieldId);
            if (inputField) {
                // Apply special handling
                console.log('Found contract amount field:', inputField);
                
                // Force remove any ریال text
                if (inputField.value && inputField.value.includes('ریال')) {
                    inputField.value = inputField.value.replace(/ریال/g, '').trim();
                }
                
                // Remove any non-numeric characters except commas
                inputField.value = inputField.value.replace(/[^\d,]/g, '');
                
                // Clear any CSS that might be adding the ریال symbol
                inputField.style.setProperty('padding-left', '1rem', 'important');
                inputField.style.setProperty('padding-right', '1rem', 'important');
                
                // Ensure no pseudo-elements
                const style = document.createElement('style');
                style.textContent = `
                    #${fieldId}::before, #${fieldId}::after {
                        content: none !important;
                        display: none !important;
                    }
                `;
                document.head.appendChild(style);
                
                // Add custom class for targeting
                inputField.classList.add('currency-input-fixed');
                
                // Setup with basic formatter
                setupBasicCurrencyField(inputField);
            }
        }
    }
    
    // Also try direct ID-based approach
    const moneyFieldsById = document.querySelectorAll('input[id*="amount"], input[id*="price"]');
    moneyFieldsById.forEach(field => {
        // Force remove any ریال text
        if (field.value && field.value.includes('ریال')) {
            field.value = field.value.replace(/ریال/g, '').trim();
        }
        
        // Apply styling to prevent pseudo-elements
        field.style.setProperty('padding-left', '1rem', 'important');
        field.style.setProperty('padding-right', '1rem', 'important');
        
        // Setup with basic formatter if not already
        if (!field.classList.contains('currency-input-enhanced')) {
            field.classList.add('currency-input-fixed');
            setupBasicCurrencyField(field);
        }
    });
}

// Exclude contractor_name field from currency formatting
function excludeContractorNameField() {
    const contractorFields = document.querySelectorAll('input[name="contractor_name"], input[id="contractor_name"]');
    contractorFields.forEach(field => {
        // Remove any currency classes
        field.classList.remove('currency-input', 'currency-input-enhanced', 'currency-input-fixed');
        
        // Add exclusion attributes
        field.setAttribute('data-exclude-currency', 'true');
        field.classList.add('text-field-only');
        
        // Remove any currency formatting
        if (field.value && field.value.includes('ریال')) {
            field.value = field.value.replace(/ریال/g, '').trim();
        }
        
        // Remove commas if they were added by currency formatter
        if (field.value && field.value.includes(',') && field.value.match(/^[\d,]+$/)) {
            // Only remove commas if the value is purely numeric with commas
            const hasOnlyDigitsAndCommas = /^[\d,]+$/.test(field.value);
            if (hasOnlyDigitsAndCommas) {
                field.value = field.value.replace(/,/g, '');
            }
        }
        
        // Apply styling to ensure normal text field appearance
        field.style.setProperty('padding-left', '12px', 'important');
        field.style.setProperty('padding-right', '12px', 'important');
        
        // Add CSS to prevent pseudo-elements
        const style = document.createElement('style');
        style.textContent = `
            input[name="contractor_name"]::before,
            input[name="contractor_name"]::after,
            input[id="contractor_name"]::before,
            input[id="contractor_name"]::after {
                content: none !important;
                display: none !important;
            }
        `;
        if (!document.querySelector('style[data-contractor-exclude]')) {
            style.setAttribute('data-contractor-exclude', 'true');
            document.head.appendChild(style);
        }
        
        console.log('Excluded contractor field from currency formatting:', field);
    });
}

// Cleanup function
function cleanupCurrencyFormatters() {
    autoNumericInstances.forEach((instance, element) => {
        try {
            instance.remove();
        } catch (e) {
            console.warn('Error removing autoNumeric instance:', e);
        }
    });
    autoNumericInstances.clear();
}

// Initialize enhanced currency formatting
async function initializeEnhancedCurrencyFormatting() {
    try {
        // First exclude contractor name field from any processing
        excludeContractorNameField();
        
        // Direct fix for contract amount field
        fixContractAmountField();
        
        // Process money fields to ensure no ریال in inputs
        processMoneyCurrencyFields();
        
        // Setup existing currency input containers
        await setupEnhancedCurrencyContainer();
        
        // Auto-detect currency fields
        await autoDetectCurrencyFields();
        
        // Format read-only displays
        formatReadOnlyCurrencyDisplays();
        
        // Exclude contractor name field again after all processing
        excludeContractorNameField();
        
        console.log('Enhanced currency formatting initialized successfully');
        
        // Set up MutationObserver to watch for dynamically added fields
        setupMutationObserver();
    } catch (error) {
        console.error('Error initializing enhanced currency formatting:', error);
    }
}

// Set up mutation observer to watch for dynamically added fields
function setupMutationObserver() {
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                // Check for new input fields
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // Check if the node itself is an input
                        if (node.tagName === 'INPUT') {
                            processSingleInput(node);
                        }
                        
                        // Check if the node contains inputs
                        const inputs = node.querySelectorAll('input');
                        inputs.forEach(processSingleInput);
                    }
                });
            }
        });
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    function processSingleInput(input) {
        // Skip if already processed
        if (input.classList.contains('currency-input-enhanced') || 
            input.classList.contains('currency-input-fixed')) {
            return;
        }
        
        // Check if it's a money-related field
        const name = input.name || '';
        const id = input.id || '';
        
        if (name.includes('amount') || name.includes('price') || 
            name.includes('cost') || name.includes('budget') || 
            name.includes('payment') || name.includes('fee') ||
            id.includes('amount') || id.includes('price') || 
            id.includes('cost') || id.includes('budget') || 
            id.includes('payment') || id.includes('fee')) {
            
            // Force remove any ریال text
            if (input.value && input.value.includes('ریال')) {
                input.value = input.value.replace(/ریال/g, '').trim();
            }
            
            // Apply basic formatting
            input.classList.add('currency-input-fixed');
            setupBasicCurrencyField(input);
        }
    }
}

// Legacy compatibility functions
function formatNumberWithCommas(number) {
    if (!number) return '';
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function parseFormattedNumber(formattedNumber) {
    if (!formattedNumber) return '';
    return formattedNumber.replace(/[^\d]/g, '');
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initializeEnhancedCurrencyFormatting);

// Add a backup initialization after a short delay to ensure it runs
setTimeout(initializeEnhancedCurrencyFormatting, 1000);

// Cleanup on page unload
window.addEventListener('beforeunload', cleanupCurrencyFormatters);

// Export for global access
window.CurrencyFormatter = {
    setupEnhancedCurrencyField,
    formatNumberWithCommas,
    parseFormattedNumber,
    initializeEnhancedCurrencyFormatting,
    fixContractAmountField,
    rialConfig
};
