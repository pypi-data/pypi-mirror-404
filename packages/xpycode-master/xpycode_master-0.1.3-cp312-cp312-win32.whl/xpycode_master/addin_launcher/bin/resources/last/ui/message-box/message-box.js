// Message Box Module using Office Dialog API
// Opens a separate dialog window that works even when taskpane is closed

import { computeDialogOptions } from '../../utils/index.js'; 

const waitingMessages = [];

let currentDialog = null;

/**
 * Show a message box dialog using Office.context.ui.displayDialogAsync
 * This works even when the taskpane is closed because it opens a separate window.
 * 
 * @param {string} message - The message to display
 * @param {string} title - The dialog title (default: 'XPyCode')
 * @param {string} msgType - Message type: 'Info', 'Warning', 'Error' (default: 'Info')
 */
export function showMessageBox(message, title = 'XPyCode', msgType = 'Info') {
    // Close any existing dialog first
    if (currentDialog) {
        waitingMessages.push({ message, title, msgType });
        return;
    }
    
    // Encode message as base64 to handle special characters in URL
    let encodedMessage;
    let encodingType = 'base64';

    encodedMessage = encodeURIComponent(message);
    encodingType = 'uri';
    /*
    try {
        encodedMessage = btoa(encodeURIComponent(message));
    } catch (e) {
        // Fallback if btoa fails (e.g., Unicode characters outside Latin1 range)
        window.logToServer('ERROR', 'Failed to encode message, using fallback:', e);
        encodedMessage = encodeURIComponent(message);
        encodingType = 'uri';
    }
    */
    const encodedTitle = encodeURIComponent(title);
    const type = msgType.toLowerCase();
    
    // Build dialog URL - use same origin as add-in
    const baseUrl = window.location.origin;
    const dialogUrl = `${baseUrl}/message-box-dialog.html?message=${encodedMessage}&title=${encodedTitle}&type=${type}&encoding=${encodingType}`;
    
    window.logToServer('DEBUG', 'Opening message box dialog:', title, type);
    
    // Dialog options
    const dialogOptions = computeDialogOptions(message, title);

        /* old code with fixed options:*/
        /*
        {
        height: 30,  // Percentage of screen height
        width: 30,   // Percentage of screen width
        displayInIframe: false  // Use separate window, not iframe
        }*/



    // Check if Office.context.ui is available
    if (!Office || !Office.context || !Office.context.ui || !Office.context.ui.displayDialogAsync) {
        window.logToServer('ERROR', 'Office Dialog API not available, falling back to DOM dialog');
        // Fallback to DOM-based dialog if taskpane is open
        showDomDialog(message, title, msgType);
        return;
    }
    
    // Open dialog
    Office.context.ui.displayDialogAsync(dialogUrl, dialogOptions, function(asyncResult) {
        if (asyncResult.status === Office.AsyncResultStatus.Failed) {
            window.logToServer('ERROR', 'Failed to open dialog:', asyncResult.error.code, asyncResult.error.message);
            // Put message in queue to try again later
            waitingMessages.push({ message, title, msgType });
            return;
        }
        
        currentDialog = asyncResult.value;
        window.logToServer('DEBUG', 'Message box dialog opened successfully');
        
        // Handle messages from dialog
        currentDialog.addEventHandler(Office.EventType.DialogMessageReceived, function(arg) {
            try {
                const messageData = JSON.parse(arg.message);
                if (messageData.action === 'close') {
                    try {
                        currentDialog.close();
                    }
                    finally {
                        currentDialog = null;
                        setTimeout(() => {
                            resumeNextDialog();
                        }, 300);
                    }
                }
            } catch (e) {
                window.logToServer('DEBUG', 'Dialog message:', arg.message);
            }
        });
        
        // Handle dialog closed by user (X button)
        currentDialog.addEventHandler(Office.EventType.DialogEventReceived, function(arg) {
            window.logToServer('DEBUG', 'Dialog event:', arg.error);
            currentDialog = null;
        });
    });
}

function resumeNextDialog() {
    if (waitingMessages.length === 0) return;
    const next = waitingMessages.shift();
    showMessageBox(next.message, next.title, next.msgType);
}

export function flushMessageBoxQueue() {
    waitingMessages.length = 0;
}

/**
 * Fallback DOM-based dialog for when Office Dialog API is not available
 * or when taskpane is known to be open
 */
function showDomDialog(message, title, msgType) {
    const dialog = document.getElementById('xpycode-message-box');
    const titleEl = document.getElementById('xpycode-message-box-title');
    const messageEl = document.getElementById('xpycode-message-box-text');
    const iconEl = document.getElementById('xpycode-message-box-icon');
    const dialogContent = dialog?.querySelector('.dialog');
    
    if (!dialog || !titleEl || !messageEl) {
        window.logToServer('ERROR', 'DOM message box elements not found');
        return;
    }
    
    // Set title and message
    titleEl.textContent = title;
    messageEl.textContent = message;
    
    // Remove previous type classes
    dialogContent?.classList.remove('message-box-info', 'message-box-warning', 'message-box-error');
    
    // Set icon and styling based on type
    const normalizedType = msgType.toLowerCase();
    let iconHtml = '';
    let typeClass = 'message-box-info';
    
    switch (normalizedType) {
        case 'warning':
            iconHtml = '⚠️';
            typeClass = 'message-box-warning';
            break;
        case 'error':
            iconHtml = '❌';
            typeClass = 'message-box-error';
            break;
        case 'info':
        default:
            iconHtml = 'ℹ️';
            typeClass = 'message-box-info';
            break;
    }
    
    if (iconEl) {
        iconEl.textContent = iconHtml;
    }
    dialogContent?.classList.add(typeClass);
    
    // Show dialog
    dialog.style.display = 'flex';
}

/**
 * Close the message box dialog
 */
export function closeMessageBox() {
    // Close Office dialog if open
    if (currentDialog) {
        try {
            currentDialog.close();
        } catch (e) {
            // Ignore errors
        }
        currentDialog = null;
    }
    
    // Also close DOM dialog if visible
    const dialog = document.getElementById('xpycode-message-box');
    if (dialog) {
        dialog.style.display = 'none';
    }
}

/**
 * Initialize the message box event handlers (for DOM fallback)
 * Call this once during add-in initialization
 */
export function initMessageBox() {
    const okBtn = document.getElementById('xpycode-message-box-ok');
    const dialog = document.getElementById('xpycode-message-box');
    
    if (!okBtn || !dialog) {
        window.logToServer('DEBUG', 'DOM message box elements not found, skipping init (this is OK if using Dialog API)');
        return;
    }
    
    // Close on OK button click
    okBtn.addEventListener('click', closeMessageBox);
    
    // Close on overlay click
    dialog.addEventListener('click', function(e) {
        if (e.target === dialog) {
            closeMessageBox();
        }
    });
    
    window.logToServer('DEBUG', 'DOM message box initialized (fallback)');
}

// Export for backwards compatibility
export const MessageBoxType = {
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'error'
};
