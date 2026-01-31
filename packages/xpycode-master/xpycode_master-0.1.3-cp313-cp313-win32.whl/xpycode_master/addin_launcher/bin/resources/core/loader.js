/**
 * Dynamic Module Loader
 * 
 * Handles loading of versioned modules with retry logic.
 * 
 * IMPORTANT: This file is in core/ and MUST maintain retrocompatibility.
 * Any changes must be backward compatible with older versions.
 */

import { discoverWatchdog, normalizeVersion, getVersionBasePath } from './version-detector.js';

// Maximum retry attempts before showing error
const MAX_RETRIES = 5;

// Delay between retries (ms)
const RETRY_DELAY = 2000;

// UI Elements
let loaderContainer = null;
let loaderStatus = null;
let errorContainer = null;
let errorMessage = null;
let retryButton = null;

/**
 * Initialize loader UI elements
 */
function initLoaderUI() {
    loaderContainer = document.getElementById('loader-container');
    loaderStatus = document.getElementById('loader-status');
    errorContainer = document.getElementById('error-container');
    errorMessage = document.getElementById('error-message');
    retryButton = document.getElementById('retry-button');
}

/**
 * Show loading state with message
 * @param {string} message - Status message to display
 */
export function showLoader(message) {
    if (!loaderContainer) initLoaderUI();
    
    if (loaderContainer) {
        loaderContainer.style.display = 'flex';
    }
    if (loaderStatus) {
        loaderStatus.textContent = message;
    }
    if (errorContainer) {
        errorContainer.style.display = 'none';
    }
}

/**
 * Show error state with message and retry button
 * @param {string} message - Error message to display
 * @param {Function} retryCallback - Function to call when retry is clicked
 */
export function showError(message, retryCallback) {
    if (!loaderContainer) initLoaderUI();
    
    if (loaderContainer) {
        loaderContainer.style.display = 'none';
    }
    if (errorContainer) {
        errorContainer.style.display = 'flex';
    }
    if (errorMessage) {
        errorMessage.textContent = message;
    }
    if (retryButton && retryCallback) {
        retryButton.onclick = retryCallback;
    }
}

/**
 * Hide loader and show main content
 */
export function hideLoader() {
    if (!loaderContainer) initLoaderUI();
    
    if (loaderContainer) {
        loaderContainer.style.display = 'none';
    }
    if (errorContainer) {
        errorContainer.style.display = 'none';
    }
}

/**
 * Sleep for specified milliseconds
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise<void>}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Discover watchdog with retry logic
 * @returns {Promise<Object>} - Watchdog info
 * @throws {Error} - If max retries exceeded
 */
async function discoverWithRetry() {
    let retryCount = 0;
    
    while (retryCount < MAX_RETRIES) {
        showLoader(`Discovering XPyCode server... (attempt ${retryCount + 1}/${MAX_RETRIES})`);
        
        const watchdogInfo = await discoverWatchdog();
        if (watchdogInfo) {
            return watchdogInfo;
        }
        
        retryCount++;
        if (retryCount < MAX_RETRIES) {
            showLoader(`Server not found, retrying in ${RETRY_DELAY / 1000}s...`);
            await sleep(RETRY_DELAY);
        }
    }
    
    throw new Error('Could not find XPyCode server after multiple attempts');
}

/**
 * Load and initialize the versioned main module
 * @returns {Promise<void>}
 */
export async function loadVersionedApp() {
    try {
        // Discover watchdog
        const watchdogInfo = await discoverWithRetry();
        
        // Normalize version and get base path
        const version = normalizeVersion(watchdogInfo.version);
        const basePath = getVersionBasePath(version);
        
        showLoader(`Loading XPyCode v${version}...`);
        
        // Dynamically import the main module
        const mainModule = await import(`../${basePath}/taskpane-main.js`);
        
        // Hide loader
        hideLoader();
        
        // Initialize the app
        if (mainModule.initializeApp) {
            await mainModule.initializeApp(watchdogInfo);
        } else if (mainModule.default) {
            await mainModule.default(watchdogInfo);
        }
        
    } catch (error) {
        console.error('[XPyCode Loader] Error:', error);
        showError(
            error.message || 'Failed to load XPyCode',
            () => loadVersionedApp()  // Retry callback
        );
    }
}
