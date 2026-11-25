(function () {
    const form = document.querySelector('.domain-name-form');
    if (!form) {
        return;
    }

    const query = form.elements.namedItem('name');
    const error = form.querySelector('.domain-name-search-error');

    form.addEventListener('input', function () {
        error.hidden = true;
    });

    form.addEventListener('submit', function (event) {
        query.value = query.value.trim();
        if (!query.value || !form.querySelector('[name="domain_types"]:checked')) {
            event.preventDefault();
            error.hidden = false;
            const field = query.value ? form.querySelector('[name="domain_types"]') : query;
            field.focus();
        }
    });
})();
