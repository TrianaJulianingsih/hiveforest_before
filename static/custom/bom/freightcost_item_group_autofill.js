(function () {
    function getPackagingField(inline) {
        return inline ? inline.querySelector('select[name$="-packaging_type"]') : null;
    }

    function hasMeaningfulValue(element) {
        return !!(element && element.value && String(element.value).trim());
    }

    function shouldInitializeAutofill(productField) {
        if (!productField) {
            return false;
        }

        var inline = productField.closest('.inline-related');
        if (!inline) {
            return false;
        }

        var packagingField = getPackagingField(inline);
        var itemGroupField = inline.querySelector('select[name$="-item_group"]');
        var groupProdukField = inline.querySelector('select[name$="-group_produk"], input[name$="-group_produk"], textarea[name$="-group_produk"]');

        return hasMeaningfulValue(productField) && (
            !hasMeaningfulValue(packagingField)
            || !hasMeaningfulValue(itemGroupField)
            || !hasMeaningfulValue(groupProdukField)
        );
    }

    function scheduleUpdate(productField) {
        window.setTimeout(function () {
            updateItemGroup(productField);
        }, 50);
    }

    function getLookupUrl(productId) {
        if (!productId) {
            return null;
        }

        var basePath = window.location.pathname.replace(/(add\/|(\d+)\/change\/).*$/, '');
        return basePath + 'product-subgroup/' + productId + '/';
    }

    function triggerChange(element) {
        element.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function updatePackagingDisplay(inline, packagingId, packagingName) {
        if (!inline) {
            return;
        }

        var packagingField = getPackagingField(inline);
        if (packagingField) {
            var currentValue = packagingField.value || '';
            var autoFilledValue = packagingField.dataset.autoFilledValue || '';
            var wasManuallyChanged = packagingField.dataset.manualSelected === '1';

            if (wasManuallyChanged && currentValue && currentValue !== autoFilledValue) {
                return;
            }

            if (!packagingId && currentValue) {
                packagingField.dataset.autoFilledValue = currentValue;
                return;
            }

            packagingField.value = packagingId ? String(packagingId) : '';
            packagingField.dataset.autoFilledValue = packagingField.value || '';
            packagingField.dataset.manualSelected = '0';
            triggerChange(packagingField);
            return;
        }

        var packagingReadonly = inline.querySelector('.field-packaging_type_display .readonly');
        if (packagingReadonly) {
            packagingReadonly.textContent = packagingName || '';
        }
    }

    function updateGroupProdukField(inline, value) {
        if (!inline) {
            return;
        }

        var groupProdukField = inline.querySelector('select[name$="-group_produk"], input[name$="-group_produk"], textarea[name$="-group_produk"]');
        if (!groupProdukField) {
            return;
        }

        groupProdukField.value = value || '';
        triggerChange(groupProdukField);
    }

    function updateItemGroup(productField) {
        if (!productField) {
            return;
        }

        var productId = productField.value;
        var inline = productField.closest('.inline-related');
        if (!inline) {
            return;
        }

        var packagingField = getPackagingField(inline);
        if (packagingField) {
            packagingField.dataset.manualSelected = '0';
        }

        var itemGroupField = inline.querySelector('select[name$="-item_group"]');
        if (!itemGroupField) {
            return;
        }

        if (!productId) {
            if (!hasMeaningfulValue(getPackagingField(inline)) && !hasMeaningfulValue(itemGroupField)) {
                updatePackagingDisplay(inline, '', '');
                updateGroupProdukField(inline, '');
                itemGroupField.value = '';
                triggerChange(itemGroupField);
            }
            return;
        }

        var lookupUrl = getLookupUrl(productId);
        if (!lookupUrl) {
            return;
        }

        fetch(lookupUrl, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(function (response) {
                return response.ok ? response.json() : null;
            })
            .then(function (response) {
                if (!response) {
                    return;
                }

                updatePackagingDisplay(inline, response.packaging_id || '', response.packaging_name || '');
                updateGroupProdukField(inline, response.group_produk_id ? String(response.group_produk_id) : '');
                itemGroupField.value = response.subgroup_id ? String(response.subgroup_id) : '';
                triggerChange(itemGroupField);
            })
            .catch(function () {
                updatePackagingDisplay(inline, '', '');
                updateGroupProdukField(inline, '');
                itemGroupField.value = '';
                triggerChange(itemGroupField);
            });
    }

    function bindProductField(productField) {
        if (!productField || productField.dataset.itemGroupAutofillBound === '1') {
            return;
        }

        productField.dataset.itemGroupAutofillBound = '1';
        productField.addEventListener('change', function () {
            scheduleUpdate(productField);
        });

        productField.addEventListener('input', function () {
            scheduleUpdate(productField);
        });

        if (window.django && window.django.jQuery) {
            window.django.jQuery(productField).on('select2:select select2:clear change', function () {
                scheduleUpdate(productField);
            });
        }

        var observer = new MutationObserver(function () {
            scheduleUpdate(productField);
        });
        observer.observe(productField, {
            attributes: true,
            childList: true,
            subtree: true,
        });
    }

    function bindPackagingField(packagingField) {
        if (!packagingField || packagingField.dataset.packagingManualBound === '1') {
            return;
        }

        packagingField.dataset.packagingManualBound = '1';
        packagingField.dataset.autoFilledValue = packagingField.value || '';
        packagingField.addEventListener('change', function () {
            var autoFilledValue = packagingField.dataset.autoFilledValue || '';
            packagingField.dataset.manualSelected = packagingField.value !== autoFilledValue ? '1' : '0';
        });
    }

    function initAllProductFields(root) {
        (root || document).querySelectorAll('select[name$="-product"]').forEach(function (field) {
            bindProductField(field);
            if (shouldInitializeAutofill(field)) {
                scheduleUpdate(field);
            }
        });

        (root || document).querySelectorAll('select[name$="-packaging_type"]').forEach(function (field) {
            bindPackagingField(field);
        });
    }

    document.addEventListener('change', function (event) {
        if (event.target && event.target.matches('select[name$="-product"]')) {
            scheduleUpdate(event.target);
        }
    });

    document.addEventListener('DOMContentLoaded', function () {
        initAllProductFields(document);

        var bodyObserver = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType !== 1) {
                        return;
                    }

                    if (node.matches && node.matches('select[name$="-product"]')) {
                        bindProductField(node);
                        scheduleUpdate(node);
                        return;
                    }

                    initAllProductFields(node);
                });
            });
        });

        bodyObserver.observe(document.body, {
            childList: true,
            subtree: true,
        });

        window.setTimeout(function () {
            initAllProductFields(document);
        }, 300);
    });
})();
