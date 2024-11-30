console.log('Initializing client management module...');

// Validation configurations
const ValidationConfig = {
    clientCode: {
        minLength: 5,
        maxLength: 10,
        pattern: /^\d+$/,
        messages: {
            pattern: 'Only digits are allowed',
            minLength: 'Must be at least 5 digits',
            maxLength: 'Cannot exceed 10 digits'
        }
    },
    iceCode: {
        length: 15,
        pattern: /^\d+$/,
        messages: {
            pattern: 'Only digits are allowed',
            length: 'Must be exactly 15 digits'
        }
    },
    accountingCode: {
        minLength: 5,
        maxLength: 7,
        pattern: /^3\d{4,6}$/,
        messages: {
            pattern: 'Must start with 3 and contain only digits',
            length: 'Must be between 5 and 7 digits'
        }
    },
    name: {
        pattern: /^[a-zA-Z\s]+$/,
        messages: {
            pattern: 'Only letters and spaces allowed'
        }
    }
};

class FormValidator {
    constructor(formId, config) {
        this.form = document.getElementById(formId);
        this.config = config;
        console.log(`Initializing validator for form: ${formId}`);
        this.setupValidation();
    }

    setupValidation() {
        const inputs = this.form.querySelectorAll('input[data-validate]');
        inputs.forEach(input => {
            console.log(`Setting up validation for: ${input.id}`);
            this.setupInputValidation(input);
        });
    }

    setupInputValidation(input) {
        const validationType = input.dataset.validate;
        const rules = this.config[validationType];

        // Real-time validation
        input.addEventListener('input', (e) => {
            console.log(`Input event on ${input.id}`);
            this.validateInput(input, rules);
        });

        // Blur validation
        input.addEventListener('blur', (e) => {
            console.log(`Blur event on ${input.id}`);
            this.validateInput(input, rules, true);
        });

        // Prevent invalid characters
        input.addEventListener('keypress', (e) => {
            if (rules.pattern && !String.fromCharCode(e.charCode).match(rules.pattern)) {
                e.preventDefault();
            }
        });
    }

    validateInput(input, rules, isBlur = false) {
        const value = input.value.trim();
        let isValid = true;
        let message = '';

        // Add validating class during check
        input.classList.add('is-validating');

        // Pattern validation
        if (rules.pattern && !value.match(rules.pattern)) {
            isValid = false;
            message = rules.messages.pattern;
        }

        // Length validation
        if (rules.length && value.length !== rules.length) {
            isValid = false;
            message = rules.messages.length;
        }

        if (rules.minLength && value.length < rules.minLength) {
            isValid = false;
            message = rules.messages.minLength;
        }

        if (rules.maxLength && value.length > rules.maxLength) {
            isValid = false;
            message = rules.messages.maxLength;
        }

        // Update UI with validation result
        setTimeout(() => {
            input.classList.remove('is-validating');
            this.updateValidationUI(input, isValid, message, isBlur);
        }, 300);

        return isValid;
    }

    updateValidationUI(input, isValid, message, isBlur) {
        const feedback = input.nextElementSibling;
        
        if (isValid) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            if (feedback && feedback.classList.contains('invalid-feedback')) {
                feedback.classList.remove('show');
            }
        } else if (isBlur || input.value.length > 0) {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
            if (feedback) {
                feedback.textContent = message;
                feedback.classList.add('show');
            }
        }
    }

    validateForm() {
        let isValid = true;
        const inputs = this.form.querySelectorAll('input[data-validate]');
        
        inputs.forEach(input => {
            const validationType = input.dataset.validate;
            const rules = this.config[validationType];
            if (!this.validateInput(input, rules, true)) {
                isValid = false;
            }
        });

        return isValid;
    }
}

// Client Management class
class ClientManagement {
    constructor() {
        console.log('Initializing ClientManagement');
        this.initializeValidators();
        this.bindEvents();
    }

    initializeValidators() {
        this.clientValidator = new FormValidator('clientForm', ValidationConfig);
        this.entityValidator = new FormValidator('entityForm', ValidationConfig);
    }

    bindEvents() {
        // Client form events
        $('#saveClientBtn').on('click', () => this.saveClient());
        $('#clientModal').on('hidden.bs.modal', () => this.resetForm('clientForm'));

        // Entity form events
        $('#saveEntityBtn').on('click', () => this.saveEntity());
        $('#entityModal').on('hidden.bs.modal', () => this.resetForm('entityForm'));
    }

    resetForm(formId) {
        console.log(`Resetting form: ${formId}`);
        const form = document.getElementById(formId);
        form.reset();
        
        const inputs = form.querySelectorAll('.form-control');
        inputs.forEach(input => {
            input.classList.remove('is-valid', 'is-invalid', 'is-validating');
            const feedback = input.nextElementSibling;
            if (feedback) {
                feedback.classList.remove('show');
            }
        });
    }

    async saveClient() {
        console.log('Attempting to save client');
        if (!this.clientValidator.validateForm()) {
            console.log('Client form validation failed');
            return;
        }

        const data = {
            name: $('#clientName').val(),
            client_code: $('#clientCode').val()
        };

        try {
            const id = $('#clientId').val();
            const method = id ? 'PUT' : 'POST';
            const url = id ? 
                `/testapp/api/clients/${id}/update/` : 
                '/testapp/api/clients/create/';

            const response = await this.sendRequest(url, method, data);
            
            if (response.ok) {
                console.log('Client saved successfully');
                $('#clientModal').modal('hide');
                this.loadClients();
                this.showToast('Success', 'Client saved successfully');
            }
        } catch (error) {
            console.error('Error saving client:', error);
            this.showToast('Error', error.message);
        }
    }

    async sendRequest(url, method, data) {
        console.log(`Sending ${method} request to ${url}`, data);
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Request failed');
        }

        return response;
    }

    showToast(title, message) {
        // Implementation depends on your toast library
        console.log(`${title}: ${message}`);
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing client management module');
    window.clientManagement = new ClientManagement();
});