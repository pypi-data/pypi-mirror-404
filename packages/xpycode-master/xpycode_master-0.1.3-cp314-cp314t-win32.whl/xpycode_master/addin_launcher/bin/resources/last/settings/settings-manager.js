// XPyCode Settings Manager Module
// Manages user settings dialog and persistence

import { setNotificationsEnabled } from '../ui/notifications.js';

// Settings constants
const SETTINGS_KEY = 'XPyCode_Settings';
const DEFAULT_SETTINGS = {
    notifications: true,
    autostart: false,
    autoscroll: true,
    wrapText: false,
    enableEditorEvents: true
};

// Current settings state
let _currentSettings = { ...DEFAULT_SETTINGS };

/**
 * Get current settings
 * @returns {Object} Current settings object (copy)
 */
export function getCurrentSettings() {
    return { ..._currentSettings };
}

/**
 * Update settings (internal use only)
 * @param {Object} newSettings - New settings to merge
 * @private
 */
function _updateSettingsInternal(newSettings) {
    _currentSettings = { ...DEFAULT_SETTINGS, ...newSettings };
}

/**
 * Get a specific setting value
 * @param {string} key - Setting key
 * @returns {*} Setting value
 */
export function getSetting(key) {
    return _currentSettings[key];
}

/**
 * Set a specific setting value
 * @param {string} key - Setting key
 * @param {*} value - Setting value
 */
export function setSetting(key, value) {
    _currentSettings[key] = value;
    // Update global window.currentSettings
    if (typeof window !== 'undefined') {
        window.currentSettings = { ..._currentSettings };
    }
}

/**
 * Load settings from Office storage
 */
export function loadSettings() {
    try {
        if (Office.context?.document?.settings) {
            const savedJson = Office.context.document.settings.get(SETTINGS_KEY);
            if (savedJson) {
                _updateSettingsInternal(JSON.parse(savedJson));
            }
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error loading settings:', err);
    }
    applySettings();
}

/**
 * Save settings to Office storage
 */
export function saveSettings() {
    try {
        if (Office.context?.document?.settings) {
            Office.context.document.settings.set(SETTINGS_KEY, JSON.stringify(_currentSettings));
            Office.context.document.settings.saveAsync();
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error saving settings:', err);
    }
}

/**
 * Set console wrap text behavior
 * @param {boolean} enabled - Whether to wrap text in console
 */
export function setConsoleWrapText(enabled) {
    const consoleOutput = document.getElementById('console-output');
    if (consoleOutput) {
        if (enabled) {
            // Wrap text, no horizontal scroll
            consoleOutput.style.whiteSpace = 'pre-wrap';
            consoleOutput.style.overflowX = 'hidden';
        } else {
            // Don't wrap text, show horizontal scroll
            consoleOutput.style.whiteSpace = 'pre';
            consoleOutput.style.overflowX = 'auto';
        }
    }
}

/**
 * Apply settings to the application
 */
export function applySettings() {
    setNotificationsEnabled(_currentSettings.notifications);
    setConsoleWrapText(_currentSettings.wrapText);
    // Update global window.currentSettings for message handlers
    if (typeof window !== 'undefined') {
        window.currentSettings = { ..._currentSettings };
    }
    // Note: setStartupBehavior will be called explicitly when settings are saved
}

/**
 * Set startup behavior for the add-in
 * @param {boolean} startOnOpen - Whether to start the add-in on workbook open
 */
export async function setStartupBehavior(startOnOpen) {
    try {
        if (Office.addin?.setStartupBehavior) {
            const behavior = startOnOpen ? Office.StartupBehavior.load : Office.StartupBehavior.none;
            await Office.addin.setStartupBehavior(behavior);
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error setting startup behavior:', err);
    }
}

/**
 * Open the settings dialog
 */
export function openSettingsDialog() {
    const notificationsEl = document.getElementById('setting-notifications');
    const autostartEl = document.getElementById('setting-autostart');
    const autoscrollEl = document.getElementById('setting-autoscroll');
    const wrapTextEl = document.getElementById('setting-wraptext');
    const enableEditorEventsEl = document.getElementById('setting-enable-editor-events');
    const overlayEl = document.getElementById('settings-overlay');
    
    if (notificationsEl) notificationsEl.checked = _currentSettings.notifications;
    if (autostartEl) autostartEl.checked = _currentSettings.autostart;
    if (autoscrollEl) autoscrollEl.checked = _currentSettings.autoscroll;
    if (wrapTextEl) wrapTextEl.checked = _currentSettings.wrapText;
    if (enableEditorEventsEl) enableEditorEventsEl.checked = _currentSettings.enableEditorEvents;
    if (overlayEl) overlayEl.style.display = 'flex';
}

/**
 * Close the settings dialog
 */
export function closeSettingsDialog() {
    const overlayEl = document.getElementById('settings-overlay');
    if (overlayEl) overlayEl.style.display = 'none';
}

/**
 * Save settings from the dialog form
 */
export function saveSettingsFromDialog() {
    const notificationsEl = document.getElementById('setting-notifications');
    const autostartEl = document.getElementById('setting-autostart');
    const autoscrollEl = document.getElementById('setting-autoscroll');
    const wrapTextEl = document.getElementById('setting-wraptext');
    const enableEditorEventsEl = document.getElementById('setting-enable-editor-events');
    
    if (notificationsEl) _currentSettings.notifications = notificationsEl.checked;
    if (autostartEl) _currentSettings.autostart = autostartEl.checked;
    if (autoscrollEl) _currentSettings.autoscroll = autoscrollEl.checked;
    if (wrapTextEl) _currentSettings.wrapText = wrapTextEl.checked;
    if (enableEditorEventsEl) _currentSettings.enableEditorEvents = enableEditorEventsEl.checked;
    
    saveSettings();
    applySettings();
    setStartupBehavior(_currentSettings.autostart);
    closeSettingsDialog();
}
