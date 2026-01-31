// Toolbar action functions

/**
 * Check if websocket connection is open
 * @returns {boolean} True if connected, false otherwise
 */
export function isConnectedToServer() {
    return window._xpycode_messaging && 
           window._xpycode_messaging.isOpen();
}

/**
 * Send show_ide message to business layer
 * @returns {Promise<boolean>} True if message sent successfully, false otherwise
 */
export async function sendShowIDEMessage() {
    try {
        // Check if websocket is connected
        if (!window._xpycode_messaging || !isConnectedToServer()) {
            window.logToServer('DEBUG', 'Initializing connection for IDE...');
            // Wait a bit for connection to be established
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check again
            if (!isConnectedToServer()) {
                window.logToServer('ERROR', 'Cannot show IDE: not connected to business layer');
                return false;
            }
        }
        
        // Send show_ide message to business layer
        window.logToServer('DEBUG', 'Sending show_ide message');
        window._xpycode_messaging.sendRaw({
            type: "show_ide"
        });
        
        return true;
    } catch (error) {
        window.logToServer('ERROR', "Failed to show IDE:", error);
        return false;
    }
}

/**
 * Show IDE function called from ribbon button
 * @param {Office.AddinCommands.Event} event - Event object for completing the action
 */
export async function showIDE(event) {
    await sendShowIDEMessage();
    
    // Complete the action for ribbon button
    if (event && event.completed) {
        event.completed();
    }
}

/**
 * Show IDE function called from taskpane button
 */
export async function showIDEFromTaskpane() {
    await sendShowIDEMessage();
}
