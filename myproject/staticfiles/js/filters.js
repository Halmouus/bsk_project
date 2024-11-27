document.addEventListener('DOMContentLoaded', function () {
    const urlParams = new URLSearchParams(window.location.search);

    // Ensure filters remain visible if any are applied
    const hasFilters = [...urlParams.entries()].some(([key, value]) => value);
    if (hasFilters) {
        document.querySelector('.filter-panel').style.display = 'block';
    }

    // Initialize checkbox states from URL params
    urlParams.forEach((value, key) => {
        const input = document.querySelector(`[name="${key}"]`);
        if (input && input.type === 'checkbox') {
            input.checked = value === '1';
        }
    });

    // Apply button logic
    document.querySelector('#apply-filters').addEventListener('click', function () {
        const form = document.querySelector('#filter-form');
        const params = new URLSearchParams(new FormData(form));
        window.location.search = params.toString();
    });

    // Reset button logic
    document.querySelector('#reset-filters').addEventListener('click', function () {
        document.querySelector('#filter-form').reset();
        window.location.search = '';
    });
});
