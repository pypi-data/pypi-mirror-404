/**
 * XPyCode Taskpane Main Module
 * 
 * Main application logic for the XPyCode taskpane.
 * This module is loaded dynamically by the loader after version detection.
 */

// Core imports (relative to this file's location in last/)
import { TEMPORARY_PARENT_ID } from './core/constants.js';
import { genId } from './core/utils.js';
import { ContextManager } from './core/context-manager.js';

// Messaging imports
import { Messaging } from './messaging/messaging.js';

// Event imports
import { EventDispatcher } from './events/event-dispatcher.js';

// UI imports
import { PythonCodeConsole } from './ui/console.js';
import { showErrorNotification } from './ui/notifications.js';
import { showIDE, showIDEFromTaskpane } from './ui/toolbar-actions.js';
import { initUsefulLinks } from './ui/useful-links.js';

// Settings imports
import { 
    loadSettings, 
    getCurrentSettings,
    openSettingsDialog, 
    closeSettingsDialog, 
    saveSettingsFromDialog 
} from './settings/index.js';

// Bindings imports
import { 
    initBindingDropdown,
    initNewBindingDialog,
    initManageBindingsDialog,
    initDeleteConfirmDialog
} from './bindings/index.js';

// Utils imports
import { initMessageDialog, reloadConfig } from './utils/index.js';

// Message Box imports
import { initMessageBox } from './ui/message-box/index.js';

// Advanced Actions imports
import { initAdvancedActions } from './advanced-actions/index.js';

// Configuration constants
const DEFAULT_SERVER_PORT = 8000;

/**
 * Generate a unique workbook ID for this session
 */
function getWorkbookId() {
    let workbookId = sessionStorage.getItem('xpycode_workbook_id');
    if (!workbookId) {
        workbookId = 'workbook_' + genId();
        sessionStorage.setItem('xpycode_workbook_id', workbookId);
    }
    return workbookId;
}

/**
 * Initialize the application
 * @param {Object} watchdogInfo - Information from the watchdog (port, version, etc.)
 */
export async function initializeApp(watchdogInfo) {
    console.log('[XPyCode] Initializing app with watchdog info:', watchdogInfo);
    
    // Show the app container
    const appContainer = document.getElementById('app-container');
    if (appContainer) {
        appContainer.style.display = 'block';
    }
    
    // Make globals available for message handlers
    window.currentSettings = getCurrentSettings();
    window.showErrorNotification = showErrorNotification;
    
    // Expose logToServer globally
    window.logToServer = (level, ...messages) => {
        if (window._xpycode_messaging && window._xpycode_messaging.isOpen()) {
            window._xpycode_messaging.logToServer(level, ...messages);
        } else {
            const msg = messages.map(m => typeof m === 'object' ? JSON.stringify(m) : String(m)).join(' ');
            switch (level) {
                case 'ERROR': console.error('[XPyCode]', msg); break;
                case 'WARNING': console.warn('[XPyCode]', msg); break;
                case 'DEBUG': console.debug('[XPyCode]', msg); break;
                default: console.log('[XPyCode]', msg); break;
            }
        }
    };
    
    // Initialize console
    const frontendPythonConsole = new PythonCodeConsole();
    
    // Load config params
    await reloadConfig();
    
    // Initialize UI
    const ctxMgr = new ContextManager();
    ctxMgr.ensureContext();
    
    // Connect through Business Layer with workbook ID
    const workbookId = getWorkbookId();
    
    // Get workbook name using recommended Excel.run pattern
    let workbookName = 'Untitled';
    try {
        await Excel.run(async (context) => {
            context.workbook.load("name");
            await context.sync();
            workbookName = context.workbook.name || 'Untitled';
        });
        window.logToServer('DEBUG', 'Workbook name retrieved:', workbookName);
    } catch (err) {
        window.logToServer('WARNING', 'Could not retrieve workbook name:', err);
    }
    
    // Get server port from config or use default
    const server_port = (window.XPYCODE_CONFIG && window.XPYCODE_CONFIG.serverPort) || DEFAULT_SERVER_PORT;
    const server_host = 'localhost';
    
    window.logToServer('DEBUG', 'Connecting to Business Layer:', server_host, server_port, workbookId, workbookName);
    
    const messaging = new Messaging(server_host, server_port, workbookId, workbookName, ctxMgr, frontendPythonConsole);
    
    // Store global reference for Python_Function calls
    window._xpycode_messaging = messaging;
    
    // Create EventDispatcher and link it with Messaging
    const eventDispatcher = new EventDispatcher(ctxMgr, messaging);
    messaging.setEventDispatcher(eventDispatcher);
    
    frontendPythonConsole.init();
    frontendPythonConsole.setConnected(false);
    
    // Get Office info for logging
    const info = Office.context.host;
    if (info === Office.HostType.Excel) {
        frontendPythonConsole.log('XPyCode initialized in Excel');
    } else {
        frontendPythonConsole.log('XPyCode initialized (Host: ' + info + ')');
    }
    
    messaging.connect()
        .catch((err) => {
            window.logToServer('ERROR', 'Unable to connect to Business Layer', err);
            frontendPythonConsole.setConnected(false);
            frontendPythonConsole.setStatus('Unable to connect to Business Layer. See console for details.', 'error');
            frontendPythonConsole.log('Unable to connect to Business Layer. See browser console for details.', 'error');
        });
    
    // Setup event listeners
    const cleanBtn = document.getElementById('clean-console-btn');
    if (cleanBtn) {
        cleanBtn.addEventListener('click', function() {
            frontendPythonConsole.clear();
        });
    }
    
    // Setup Show Editor button
    const showEditorBtn = document.getElementById('show-editor-btn');
    if (showEditorBtn) {
        showEditorBtn.addEventListener('click', showIDEFromTaskpane);
    }
    
    // Setup Documentation button
    const docsBtn = document.getElementById('btn-docs');
    if (docsBtn) {
        docsBtn.addEventListener('click', function() {
            const config = window.XPYCODE_CONFIG;
            let docsUrl = 'https://docs.xpycode.com';
            if (config && config.docsPort) {
                if (config.docsPort > -1) {
                    docsUrl = `http://127.0.0.1:${config.docsPort}/`;
                }
                window.open(docsUrl, '_blank');
            } else {
                window.logToServer('WARNING', 'Documentation port not available in config');
                frontendPythonConsole.log('Documentation server is not running or port not configured.', 'warning');
            }
        });
    }
    
    // Setup error indicator click handler
    const errorIndicator = document.getElementById('error-indicator');
    if (errorIndicator) {
        errorIndicator.addEventListener('click', function() {
            const consoleOutput = document.getElementById('console-output');
            if (consoleOutput) {
                consoleOutput.scrollTop = consoleOutput.scrollHeight;
            }
            errorIndicator.style.display = 'none';
        });
    }
    
    // Setup settings button
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', openSettingsDialog);
    }
    
    // Setup settings dialog
    const settingsClose = document.getElementById('settings-close');
    if (settingsClose) {
        settingsClose.addEventListener('click', closeSettingsDialog);
    }
    
    const settingsSave = document.getElementById('settings-save');
    if (settingsSave) {
        settingsSave.addEventListener('click', saveSettingsFromDialog);
    }
    
    const settingsCancel = document.getElementById('settings-cancel');
    if (settingsCancel) {
        settingsCancel.addEventListener('click', closeSettingsDialog);
    }
    
    // Close settings dialog when clicking overlay
    const settingsOverlay = document.getElementById('settings-overlay');
    if (settingsOverlay) {
        settingsOverlay.addEventListener('click', function(e) {
            if (e.target === settingsOverlay) {
                closeSettingsDialog();
            }
        });
    }
    
    // Load settings
    loadSettings();
    
    // Initialize useful links
    initUsefulLinks();
    
    // Initialize binding management
    initBindingDropdown();
    initNewBindingDialog();
    initManageBindingsDialog();
    initDeleteConfirmDialog();
    initMessageDialog();
    initMessageBox();
    
    // Initialize advanced actions
    initAdvancedActions();
    
    async function finishInitialization() {
        try {
            await Excel.run(context => {
                const sheet = context.workbook.worksheets.getActiveWorksheet();
                window.isInitialized = true;
            });
        } catch (err) {
        }
        if (!window.isInitialized) {
            await setTimeout(finishInitialization, 500);
        }
    }
    await finishInitialization();
    
    // Register the function for the ribbon button
    Office.actions.associate("showIDE", showIDE);
}

// Default export for compatibility
export default initializeApp;
