/**
 * Editor Bridge Script
 * Handles auto-loading save files and intercepting downloads for pywebview integration.
 */

(function () {
    'use strict';

    /**
     * Attempt to auto-load the file from the Python backend.
     */
    async function tryLoadFile() {
        if (typeof pywebview === 'undefined') {
            setTimeout(tryLoadFile, 500);
            return;
        }

        try {
            const b64 = await pywebview.api.get_file_data();
            const fileName = await pywebview.api.get_file_name();
            if (!b64) return;

            const binary = atob(b64);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {
                bytes[i] = binary.charCodeAt(i);
            }

            const file = new File([bytes], fileName, { type: 'application/octet-stream' });
            const input = document.querySelector('input[type="file"]');
            if (input) {
                const dt = new DataTransfer();
                dt.items.add(file);
                input.files = dt.files;
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        } catch (e) {
            console.error('Auto-load failed:', e);
        }
    }

    /**
     * Create and show an overlay with a message.
     * @param {string} html - HTML content for the overlay
     * @returns {HTMLElement} The overlay element
     */
    function createOverlay(html) {
        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.9);display:flex;align-items:center;justify-content:center;z-index:99999;';
        overlay.innerHTML = html;
        document.body.appendChild(overlay);
        return overlay;
    }

    /**
     * Show a success message overlay.
     * @param {HTMLElement} overlay - The overlay element to update
     */
    function showSuccess(overlay) {
        overlay.innerHTML = '<div style="text-align:center;color:#4CAF50;font-size:28px;">✅ Save Updated!<br><small style="font-size:16px;">Closing...</small></div>';
    }

    /**
     * Show an error message overlay.
     * @param {HTMLElement} overlay - The overlay element to update
     * @param {string} message - Error message to display
     */
    function showError(overlay, message) {
        overlay.innerHTML = '<div style="text-align:center;color:#f44336;font-size:28px;">❌ Error<br><small style="font-size:14px;">' + message + '</small></div>';
    }

    /**
     * Intercept download link clicks to save via Python backend.
     */
    function interceptDownloads() {
        document.addEventListener('click', async function (e) {
            const target = e.target;
            if (target.tagName !== 'A' || !target.hasAttribute('download')) {
                return;
            }

            e.preventDefault();
            e.stopPropagation();

            const overlay = createOverlay(
                '<div style="text-align:center;color:white;font-size:28px;">💾 Saving...<br><small style="font-size:16px;">Please wait</small></div>'
            );

            const href = target.href;
            if (!href || !href.startsWith('blob:')) {
                showError(overlay, 'Invalid download link');
                setTimeout(() => overlay.remove(), 3000);
                return;
            }

            try {
                const response = await fetch(href);
                const blob = await response.blob();
                const reader = new FileReader();

                reader.onload = async function () {
                    try {
                        const b64 = reader.result.split(',')[1];
                        const result = await pywebview.api.save_edited_file(b64);

                        if (result.success) {
                            showSuccess(overlay);
                            setTimeout(async () => {
                                await pywebview.api.close_window();
                            }, 1500);
                        } else {
                            showError(overlay, result.error);
                            setTimeout(() => overlay.remove(), 3000);
                        }
                    } catch (err) {
                        showError(overlay, err.message);
                        setTimeout(() => overlay.remove(), 3000);
                    }
                };
                reader.readAsDataURL(blob);
            } catch (err) {
                showError(overlay, err.message);
                setTimeout(() => overlay.remove(), 3000);
            }

            return false;
        }, true);
    }

    // Initialize after DOM is ready
    setTimeout(tryLoadFile, 1000);
    setTimeout(interceptDownloads, 2000);
})();
