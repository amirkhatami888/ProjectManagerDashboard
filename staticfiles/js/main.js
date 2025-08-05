/**
 * Main JavaScript file for ProjectManagerDashboard
 * Common functionality across the application
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Auto-hide alerts after 5 seconds
    var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm delete buttons
    var deleteButtons = document.querySelectorAll('.btn-delete, .delete-btn');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('آیا از حذف این مورد اطمینان دارید؟')) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Number formatting for Persian display
    function formatPersianNumber(number) {
        return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    // Format numbers in elements with .persian-number class
    var persianNumbers = document.querySelectorAll('.persian-number');
    persianNumbers.forEach(function(element) {
        var number = parseFloat(element.textContent.replace(/,/g, ''));
        if (!isNaN(number)) {
            element.textContent = formatPersianNumber(number);
        }
    });

    // Loading state for forms
    var submitButtons = document.querySelectorAll('form button[type="submit"]');
    submitButtons.forEach(function(button) {
        button.closest('form').addEventListener('submit', function() {
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>در حال پردازش...';
        });
    });

    // Back button functionality
    var backButtons = document.querySelectorAll('.btn-back');
    backButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            window.history.back();
        });
    });

    // Print functionality
    var printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    });

    // Table row click functionality
    var clickableRows = document.querySelectorAll('tr[data-href]');
    clickableRows.forEach(function(row) {
        row.addEventListener('click', function() {
            window.location.href = this.dataset.href;
        });
        row.style.cursor = 'pointer';
    });

    // Search functionality
    var searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            var searchTerm = this.value.toLowerCase();
            var targetTable = document.querySelector(this.dataset.target);
            if (targetTable) {
                var rows = targetTable.querySelectorAll('tbody tr');
                rows.forEach(function(row) {
                    var text = row.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            }
        });
    });

    // Sidebar toggle
    var sidebarToggle = document.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.querySelector('body').classList.toggle('sidebar-toggled');
            document.querySelector('.sidebar').classList.toggle('toggled');
        });
    }

    // Auto-resize textareas
    var textareas = document.querySelectorAll('textarea.auto-resize');
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        // Trigger on load
        textarea.dispatchEvent(new Event('input'));
    });

    // Protect Persian date fields from currency formatting
    function protectDateFields() {
        var dateFields = document.querySelectorAll('.persian-date, input[name*="date"], input[id*="date"]');
        dateFields.forEach(function(field) {
            // Clear any currency placeholder
            if (field.placeholder === 'مقدار به ریال') {
                field.placeholder = '';
            }
            
            // Remove any currency classes
            field.classList.remove('currency-input', 'currency-input-enhanced', 'currency-input-fixed');
            
            // Add exclusion attributes
            field.setAttribute('data-exclude-currency', 'true');
            field.classList.add('date-field-only');
            
            // Ensure no currency formatting is applied
            if (field.value && field.value.includes('ریال')) {
                field.value = field.value.replace(/ریال/g, '').trim();
            }
        });
    }
    
    // Run protection immediately and after a short delay
    protectDateFields();
    setTimeout(protectDateFields, 100);
    setTimeout(protectDateFields, 500);

    console.log('ProjectManagerDashboard: Main JavaScript loaded successfully');
});

// Global utility functions
window.ProjectManager = {
    
    // Show loading overlay
    showLoading: function() {
        var overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center';
        overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
        overlay.style.zIndex = '9999';
        overlay.innerHTML = '<div class="spinner-border text-light" role="status"><span class="visually-hidden">Loading...</span></div>';
        document.body.appendChild(overlay);
    },
    
    // Hide loading overlay
    hideLoading: function() {
        var overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    },
    
    // Show notification
    showNotification: function(message, type = 'info') {
        var alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        alertDiv.style.zIndex = '10000';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(function() {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    },
    
    // Format currency - only numeric value, CSS handles ریال symbol
    formatCurrency: function(amount) {
        if (!amount) return '0';
        
        // Convert to number if it's a string
        const numericAmount = typeof amount === 'string' ? 
            parseFloat(amount.replace(/[^\d.-]/g, '')) : amount;
        
        if (isNaN(numericAmount)) return '0';
        
        // Format with commas only, CSS pseudo-element handles ریال symbol
        return numericAmount.toLocaleString('en-US');
    }
}; 