(function () {
    const results = document.querySelector('[data-screenshot-storage]');
    const slider = results?.querySelector('[data-screenshot-slider]');
    if (!slider) {
        return;
    }

    const maxVisibility = Number(slider.max);
    const storageKey = results.dataset.screenshotStorage;
    const buttons = results.querySelectorAll('[data-blur]');
    try {
        const saved = sessionStorage.getItem(storageKey);
        if (saved && saved.trim() && Number(saved) >= 0 && Number(saved) <= maxVisibility) {
            slider.value = saved;
        }
    } catch (error) {
        // Keep the default blur when browser storage is unavailable.
    }

    function updateVisibility() {
        results.dataset.screenshotVisibility = slider.value;
        results.style.setProperty('--object-image-blur', (maxVisibility - Number(slider.value)) + 'px');
        buttons.forEach(function (button) {
            button.setAttribute('aria-pressed', String(button.dataset.blur === slider.value));
        });
    }

    function saveVisibility() {
        updateVisibility();
        try {
            sessionStorage.setItem(storageKey, slider.value);
        } catch (error) {
            // Blur controls still work when browser storage is unavailable.
        }
    }

    buttons.forEach(function (button) {
        button.addEventListener('click', function () {
            slider.value = button.dataset.blur;
            saveVisibility();
        });
    });
    slider.addEventListener('input', saveVisibility);
    updateVisibility();

    results.querySelectorAll('[data-screenshot]').forEach(function (image) {
        function showMissingScreenshot() {
            const link = image.closest('.shot');
            if (link && link.isConnected) {
                const message = document.createElement('div');
                message.className = 'no-screenshot';
                message.textContent = 'Screenshot unavailable';
                link.replaceWith(message);
            }
        }

        image.addEventListener('error', showMissingScreenshot, {once: true});
        if (image.complete && image.naturalWidth === 0 && image.currentSrc) {
            showMissingScreenshot();
        }
    });
})();
