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
        overlay.textContent = 'Error: ' + message;
        overlay.style.color = '#f44336';
        overlay.style.whiteSpace = 'pre-wrap';
    }

    function readBlob(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.onerror = () => reject(reader.error || new Error('Could not read download'));
            reader.onabort = () => reject(new Error('Download read cancelled'));
            reader.readAsDataURL(blob);
        });
    }

    /**
     * Intercept download link clicks to save via Python backend.
     */
    function interceptDownloads() {
        document.addEventListener('click', async function (e) {
            const target = e.target.closest('a');
            if (!target || !target.hasAttribute('download')) {
                return;
            }

            e.preventDefault();
            e.stopPropagation();

            const overlay = createOverlay(
                '<div style="text-align:center;color:white;font-size:28px;">💾 Saving...<br><small style="font-size:16px;">Please wait</small></div>'
            );

            // Explicit contract with saveFilePage.vue and fileHandler.vue.
            // Both payload types use application/octet-stream; unknown names fail closed.
            const fileName = target.getAttribute('download');
            const isDatabase = fileName === 'sqldb1.sqlite' || fileName === 'sqldb2.sqlite';
            const isSave = fileName === 'hlsave.sav' || fileName === 'hlcustomsave.sav';
            const href = target.href;
            try {
                if (!isDatabase && !isSave) {
                    throw new Error('Unsupported download');
                }
                if (!href || !href.startsWith('blob:')) {
                    throw new Error('Invalid download link');
                }
                const response = await fetch(href);
                const blob = await response.blob();
                const b64 = await readBlob(blob);
                const result = isDatabase
                    ? await pywebview.api.export_database(b64, fileName)
                    : await pywebview.api.save_edited_file(b64);

                if (isDatabase && result.cancelled) {
                    overlay.remove();
                } else if (!result.success) {
                    throw new Error(result.error || 'Download failed');
                } else if (isDatabase) {
                    overlay.textContent = 'Database exported: ' + fileName;
                    overlay.style.color = '#4CAF50';
                    setTimeout(() => overlay.remove(), 1500);
                } else {
                    showSuccess(overlay);
                    setTimeout(async () => {
                        await pywebview.api.close_window();
                    }, 1500);
                }
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
