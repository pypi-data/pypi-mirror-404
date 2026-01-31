// Confirmation dialog for advanced actions

let resolvePromise = null;

/**
 * Initialize the confirm dialog
 */
export function initConfirmDialog() {
    const yesBtn = document.getElementById('confirm-action-yes');
    const cancelBtn = document.getElementById('confirm-action-cancel');
    const dialog = document.getElementById('confirm-action-dialog');
    
    if (!yesBtn || !cancelBtn || !dialog) return;
    
    yesBtn.addEventListener('click', () => {
        const saveResolvePromise=resolvePromise;
		closeConfirmDialog();
        if (saveResolvePromise) saveResolvePromise(true);
    });
    
    cancelBtn.addEventListener('click', () => {
        const saveResolvePromise=resolvePromise;
        closeConfirmDialog();
        if (saveResolvePromise) saveResolvePromise(false);
    });
    
    dialog.addEventListener('click', (e) => {
        if (e.target.classList.contains('dialog-overlay')) {
			const saveResolvePromise=resolvePromise;
            closeConfirmDialog();
            if (saveResolvePromise) saveResolvePromise(false);
        }
    });
}

/**
 * Show a confirmation dialog
 * @param {string} title - Dialog title
 * @param {string} message - Dialog message
 * @returns {Promise<boolean>} True if confirmed, false otherwise
 */
export function showConfirmDialog(title, message) {
    return new Promise((resolve) => {
        resolvePromise = resolve;
        
        const dialog = document.getElementById('confirm-action-dialog');
        const titleEl = document.getElementById('confirm-action-title');
        const messageEl = document.getElementById('confirm-action-message');
        
        if (titleEl) titleEl.textContent = title;
        if (messageEl) messageEl.textContent = message;
        if (dialog) dialog.style.display = 'flex';
    });
}

/**
 * Close the confirm dialog
 */
function closeConfirmDialog() {
    const dialog = document.getElementById('confirm-action-dialog');
    if (dialog) {
        dialog.style.display = 'none';
    }
    resolvePromise = null;
}
