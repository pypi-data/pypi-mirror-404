// Generic dialog utility functions

/**
 * Show a message dialog
 * @param {string} title - Dialog title
 * @param {string} message - Dialog message
 */
export function showMessageDialog(title, message) {
    document.getElementById('message-dialog-title').textContent = title;
    document.getElementById('message-dialog-text').textContent = message;
    document.getElementById('message-dialog').style.display = 'flex';
}

/**
 * Close the message dialog
 */
export function closeMessageDialog() {
    document.getElementById('message-dialog').style.display = 'none';
}

/**
 * Initialize the message dialog event handlers
 */
export function initMessageDialog() {
    const okBtn = document.getElementById('message-dialog-ok');
    
    if (!okBtn) return;
    
    okBtn.addEventListener('click', closeMessageDialog);
    
    // Close on overlay click
    document.getElementById('message-dialog').addEventListener('click', (e) => {
        if (e.target.classList.contains('dialog-overlay')) {
            closeMessageDialog();
        }
    });
}

export function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
}

export function computeDialogOptions(message, title) {
    // Basic text heuristics (fast, no DOM needed)
    const lines = String(message).split(/\r?\n/);
    const lineCount = lines.length;
    const maxLineLen = lines.reduce((m, l) => Math.max(m, l.length), 0);

    // Use screen dimensions for consistent sizing regardless of taskpane state
    const screenW = screen.availWidth || 1920;
    const screenH = screen.availHeight || 1080;

    // Height calculation
    const baseHPx = 140;  // Base height in pixels (header + footer + padding)
    const perLinePx = 18; // Per-line height in pixels
    
    const minHPct = 15;   // Minimum height %
    const maxHPct = 60;   // Maximum height %
    
    let heightPx = baseHPx + Math.min(lineCount, 20) * perLinePx;
    let heightPct = (heightPx / screenH) * 100;
    heightPct = Math.max(minHPct, Math.min(maxHPct, heightPct));

    // Width calculation
    const baseWPx = 300;   // Base width in pixels
    const perCharPx = 7;   // Per character width in pixels
    
    const minWPct = 20;    // Minimum width %
    const maxWPct = 50;    // Maximum width %
    
    // Consider title too (dialogs with long titles look better wider)
    const effectiveLen = Math.max(maxLineLen, (title || "").length);
    let widthPx = baseWPx + Math.min(effectiveLen, 80) * perCharPx;
    let widthPct = (widthPx / screenW) * 100;
    widthPct = Math.max(minWPct, Math.min(maxWPct, widthPct));

    return {
        height: Math.round(heightPct),
        width: Math.round(widthPct),
        displayInIframe: false,
    };
}

