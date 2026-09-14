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

    function buildShortname(nameValue) {
        const normalizedName = (nameValue || '').trim();

        if (normalizedName.length <= 25) {
            return normalizedName;
        }

        return trimToLength(initials(normalizedName), 25);
    }

    function selectedOptionText(selectElement) {
        if (!selectElement || !selectElement.options || selectElement.selectedIndex < 0) {
            return '';
        }

        const option = selectElement.options[selectElement.selectedIndex];
        return option ? option.text.trim() : '';
    }

    function buildCode(applicationName, menuName) {
        const appInitials = initials(applicationName);
        const nameInitials = initials(menuName);

        if (!appInitials || !nameInitials) {
            return '';
        }

        return trimToLength('CMS-MENU-' + appInitials + '-' + nameInitials, 20);
    }

    function syncDerivedFields() {
        const nameInput = document.getElementById('id_name');
        const codeInput = document.getElementById('id_code');
        const shortnameInput = document.getElementById('id_shortname');
        const applicationSelect = document.getElementById('id_application');

        if (!nameInput || !codeInput || !shortnameInput || !applicationSelect) {
            return;
        }

        const nameValue = nameInput.value.trim();
        const applicationValue = selectedOptionText(applicationSelect);

        codeInput.value = buildCode(applicationValue, nameValue);
        shortnameInput.value = buildShortname(nameValue);

        codeInput.setAttribute('readonly', 'readonly');
        shortnameInput.setAttribute('readonly', 'readonly');
    }

    document.addEventListener('DOMContentLoaded', function() {
        const nameInput = document.getElementById('id_name');
        const codeInput = document.getElementById('id_code');
        const shortnameInput = document.getElementById('id_shortname');
        const applicationSelect = document.getElementById('id_application');

        syncDerivedFields();

        [nameInput, applicationSelect].forEach(function(element) {
            if (element) {
                element.addEventListener('input', syncDerivedFields);
                element.addEventListener('change', syncDerivedFields);
            }
        });

        if (codeInput) {
            codeInput.setAttribute('readonly', 'readonly');
        }

        if (shortnameInput) {
            shortnameInput.setAttribute('readonly', 'readonly');
        }
    });
})();
