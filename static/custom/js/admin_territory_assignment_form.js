(function() {
    function trimToLength(value, maxLength) {
        return value.length > maxLength ? value.slice(0, maxLength) : value;
    }

    function initials(value) {
        return (value || '')
            .trim()
            .split(/[\s_-]+/)
            .filter(Boolean)
            .map(function(word) {
                return word.charAt(0).toUpperCase();
            })
            .join('');
    }

    function slugify(value) {
        return (value || '')
            .trim()
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    function buildShortname(nameValue) {
        const normalizedName = (nameValue || '').trim();
        if (normalizedName.length <= 30) {
            return normalizedName;
        }
        return trimToLength(initials(normalizedName), 30);
    }

    function selectedOptionText(selectElement) {
        if (!selectElement || !selectElement.options || selectElement.selectedIndex < 0) {
            return '';
        }
        const option = selectElement.options[selectElement.selectedIndex];
        return option ? option.text.trim() : '';
    }

    function buildName(assignmentName, customerName) {
        return [assignmentName, customerName].filter(Boolean).join(' - ');
    }

    function buildCode(nameValue) {
        const nameInitials = initials(nameValue);
        if (!nameInitials) {
            return '';
        }
        return trimToLength('TA-' + nameInitials, 30);
    }

    function syncDerivedFields() {
        const nameInput = document.getElementById('id_name');
        const codeInput = document.getElementById('id_code');
        const shortnameInput = document.getElementById('id_shortname');
        const slugInput = document.getElementById('id_slug');
        const assignmentSelect = document.getElementById('id_assignment');
        const customerSelect = document.getElementById('id_customer');

        if (!nameInput || !codeInput || !shortnameInput || !slugInput) {
            return;
        }

        const assignmentName = selectedOptionText(assignmentSelect);
        const customerName = selectedOptionText(customerSelect);
        const generatedName = buildName(assignmentName, customerName);
        const nameValue = nameInput.value.trim() || generatedName;

        if (!nameInput.value.trim() && generatedName) {
            nameInput.value = generatedName;
        }

        codeInput.value = buildCode(nameValue);
        shortnameInput.value = buildShortname(nameValue);
        slugInput.value = slugify(codeInput.value || nameValue);

        codeInput.setAttribute('readonly', 'readonly');
        shortnameInput.setAttribute('readonly', 'readonly');
        slugInput.setAttribute('readonly', 'readonly');
    }

    document.addEventListener('DOMContentLoaded', function() {
        const nameInput = document.getElementById('id_name');
        const assignmentSelect = document.getElementById('id_assignment');
        const customerSelect = document.getElementById('id_customer');
        const codeInput = document.getElementById('id_code');
        const shortnameInput = document.getElementById('id_shortname');
        const slugInput = document.getElementById('id_slug');

        syncDerivedFields();

        [nameInput, assignmentSelect, customerSelect].forEach(function(element) {
            if (element) {
                element.addEventListener('input', syncDerivedFields);
                element.addEventListener('change', syncDerivedFields);
            }
        });

        [codeInput, shortnameInput, slugInput].forEach(function(element) {
            if (element) {
                element.setAttribute('readonly', 'readonly');
            }
        });
    });
})();
