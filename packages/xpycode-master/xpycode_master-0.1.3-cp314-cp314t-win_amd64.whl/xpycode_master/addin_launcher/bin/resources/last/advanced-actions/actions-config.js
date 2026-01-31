// Configuration for advanced actions tabs and actions
// Format: Map of tab_name -> [{ shortName, description, hasInput, actionFunction }]

// Utils imports
import { flushMessageBoxQueue } from '../ui/message-box/message-box.js';
import { reloadConfig } from '../utils/index.js';


/**
 * Send a message to the business layer
 * @param {string} type - Message type
 * @param {object} payload - Additional payload data
 */
function sendToBusinessLayer(type, payload = {}) {
    if (window._xpycode_messaging && window._xpycode_messaging.isOpen()) {
        window._xpycode_messaging.sendRaw({
            type: type,
            ...payload
        });
        return true;
    }
    window.logToServer('ERROR', 'Cannot send message: not connected to business layer. Please check your connection.');
    return false;
}

/**
 * Kill IDE action - sends kill_ide message to business layer
 */
function killIDEAction() {
    window.logToServer('DEBUG', 'Sending kill_ide message');
    return sendToBusinessLayer('kill_ide');
}

/**
 * Message IDE action - sends message_ide message to business layer with message content
 * @param {string} message - The message to send to IDE
 */
function messageIDEAction(message) {
    window.logToServer('DEBUG', 'Sending message_ide message:', message);
    return sendToBusinessLayer('message_ide', { message: message });
}

/**
 * Kill Master action - calls watchdog /kill endpoint
 */
async function killMasterAction() {
	await reloadConfig();
	const config = window.XPYCODE_CONFIG || {};
    const watchdogPort = config.watchdogPort;
    const authToken = config.authToken;
    
    if (!watchdogPort) {
        window.logToServer('ERROR', 'Watchdog port not configured');
        return false;
    }
    
    try {
        const response = await fetch(`http://localhost:${watchdogPort}/kill`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        const result = await response.json();
        window.logToServer('DEBUG', 'Kill response:', result);
        return response.ok;
    } catch (error) {
        window.logToServer('ERROR', 'Kill request failed:', error);
        return false;
    }
}

/**
 * Restart Master action - calls watchdog /restart endpoint
 */
async function restartMasterAction() {
	await reloadConfig();
    const config = window.XPYCODE_CONFIG || {};
    const watchdogPort = config.watchdogPort;
    const authToken = config.authToken;
    
    if (!watchdogPort) {
        window.logToServer('ERROR', 'Watchdog port not configured');
        return false;
    }
    
    try {
        const response = await fetch(`http://localhost:${watchdogPort}/restart`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        const result = await response.json();
        window.logToServer('DEBUG', 'Restart response:', result);
        return response.ok;
    } catch (error) {
        window.logToServer('ERROR', 'Restart request failed:', error);
        return false;
    }
}

export async function restartAddinAction() {
    window.logToServer('DEBUG', 'Restarting add-in by reloading the page');
    if (Office && Office.addin && Office.addin.reload) {
        Office.addin.reload();
    }
    else {
        window.location.reload();
    }
    return true;
}

/**
 * Kill Kernel action - sends kill_kernel message to business layer
 */
function killKernelAction() {
    const workbookId = window._xpycode_workbookId || '';
    window.logToServer('DEBUG', 'Sending kill_kernel message for workbook:', workbookId);
    return sendToBusinessLayer('kill_kernel', { workbook_id: workbookId });
}

// Actions configuration
// Format: Map<tabName, Array<{shortName, description, hasInput, actionFunction}>>
export const ADVANCED_ACTIONS_CONFIG = new Map([
    ['IDE', [
        {
            shortName: 'Restart IDE',
            description: 'Kill the Editor and restart it',
            hasInput: false,
            actionFunction: killIDEAction
        },
        {
            shortName: 'Message IDE',
            description: 'Send a message to the Editor',
            hasInput: true,
            actionFunction: messageIDEAction
        }
    ]],
    ['Add-in', [
        {
            shortName: 'Flush Messages',
            description: 'Delete all messages not yet displayed',
            hasInput: false,
            actionFunction: flushMessageBoxQueue
        },
        {
            shortName: 'Restart Add-in',
            description: 'Restart the add-in (Kernel will also be restarted)',
            hasInput: false,
            actionFunction: restartAddinAction
        }
    ]],
    ['Master', [
        {
            shortName: 'Kill Master',
            description: 'Kill XPyCode Master completely (Stops everything)',
            hasInput: false,
            actionFunction: killMasterAction
        },
        {
            shortName: 'Restart Master',
            description: 'Restart XPyCode Master (Stops and Restarts everything)',
            hasInput: false,
            actionFunction: restartMasterAction
        },
        {
            shortName: 'Restart Kernel',
            description: 'Stop and restart the Python Kernel',
            hasInput: false,
            actionFunction: killKernelAction
        }
    ]]
]);
