// XPyCode UI Notifications Module
// Manages error notifications and visual indicators

import { 
    NOTIFICATION_THROTTLE_MS, 
    ERROR_MESSAGE_TRUNCATE_LENGTH, 
    ERROR_INDICATOR_AUTO_HIDE_MS 
} from '../core/constants.js';

import { showMessageBox } from './message-box/message-box.js';


// Notification state
let notificationsEnabled = true;  // Will be loaded from workbook settings

// Message buffer for throttled notifications
let messageBuffer = [];
let notificationTimer = null;
let isProcessingBuffer = false;

/**
 * Enable or disable notifications
 * @param {boolean} enabled - Whether notifications should be enabled
 */
export function setNotificationsEnabled(enabled) {
    notificationsEnabled = enabled;
}

/**
 * Get current notification enabled state
 * @returns {boolean} Whether notifications are enabled
 */
export function getNotificationsEnabled() {
    return notificationsEnabled;
}

/**
 * Process the message buffer and show notifications
 * Called by the timer after NOTIFICATION_THROTTLE_MS
 */
function processMessageBuffer() {
    // Mark that we're processing to handle new messages correctly
    isProcessingBuffer = true;
    
    // Grab the current buffer and reset it
    const messagesToProcess = messageBuffer;
    messageBuffer = [];
    notificationTimer = null;
    
    if (messagesToProcess.length === 0) {
        isProcessingBuffer = false;
        return;
    }
    
    // Combine messages for display
    let combinedMessage;
	combinedMessage = messagesToProcess.join('\n');
    
    
    // Update the error indicator in the taskpane
    const errorIndicator = document.getElementById('error-indicator');
    if (errorIndicator) {
        const displayText =  '🔴 Error: ' + messagesToProcess[messagesToProcess.length-1];
        
        errorIndicator.style.display = 'block';
        errorIndicator.textContent = displayText;
        errorIndicator.title = combinedMessage;  // Full message on hover
        
        // Auto-hide after specified time
        setTimeout(() => {
            errorIndicator.style.display = 'none';
        }, ERROR_INDICATOR_AUTO_HIDE_MS);
    }
    
    // Show notification if enabled
    if (notificationsEnabled) {
        showNotification(combinedMessage);
    }
    
    isProcessingBuffer = false;
}

/**
 * Show a notification using browser Notification API or message box
 * @param {string} message - Message to display
 */
function showNotification(message) {
    // Try browser Notification API (may not work in Office context)
	showMessageBox(message, 'Python Error Message', 'Error');
	return;
    //keep the old way in case it works a day
    try {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('XPyCode Error', {
                body: message.substring(0, 100),
                icon: 'assets/icon-32.png'
            });
        } else if ('Notification' in window && Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification('XPyCode Error', {
                        body: message.substring(0, 100),
                        icon: 'assets/icon-32.png'
                    });
                } else {
                    showMessageBox(message, 'Python Error Message', 'Error');
                }
            });
        }
    } catch (err) {
        window.logToServer('DEBUG', 'Browser notification not available:', err);
    }
}

/**
 * Show an error notification
 * Buffers messages and displays them after NOTIFICATION_THROTTLE_MS
 * to avoid notification spam when multiple errors occur rapidly
 * @param {string} message - Error message to display
 */
export function showErrorNotification(message) {
    // Add message to buffer
	if (!message){return;}
    messageBuffer.push(message.trim());
    
    window.logToServer('DEBUG', `Notification buffered (${messageBuffer.length} in buffer)`);
    
    // If no timer is active, start one
    if (notificationTimer === null) {
        notificationTimer = setTimeout(() => {
            processMessageBuffer();
        }, NOTIFICATION_THROTTLE_MS);
    }
    // If a timer is already running, the message will be included when it fires
}