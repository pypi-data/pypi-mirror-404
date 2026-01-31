// XPyCode Package Storage
// Handles persistence of package lists using Office settings

/**
 * Check if Office.context.document.settings API is available
 * @returns {boolean} True if settings API is available
 */
export function isOfficeSettingsAvailable() {
    return typeof Office !== 'undefined' && 
           Office.context && 
           Office.context.document && 
           Office.context.document.settings;
}

/**
 * Safely serialize data to JSON with error handling
 * @param {*} data - Data to serialize
 * @param {string} errorContext - Context description for error messages
 * @returns {string|null} JSON string or null if serialization fails
 */
export function safeJsonStringify(data, errorContext = 'data') {
    try {
        return JSON.stringify(data);
    } catch (jsonErr) {
        window.logToServer('ERROR', `Failed to serialize ${errorContext}:`, jsonErr);
        return null;
    }
}

/**
 * Safely parse JSON with error handling
 * @param {string} jsonStr - JSON string to parse
 * @param {string} errorContext - Context description for error messages
 * @returns {*|null} Parsed data or null if parsing fails
 */
export function safeJsonParse(jsonStr, errorContext = 'data') {
    try {
        return JSON.parse(jsonStr);
    } catch (parseErr) {
        window.logToServer('ERROR', `Failed to parse ${errorContext}:`, parseErr);
        return null;
    }
}

/**
 * Save package list and python paths to workbook settings
 * @param {Array} packages - List of package objects to save
 * @param {Array} pythonPaths - List of python path objects to save (optional)
 * @returns {boolean} True if save was successful
 */
export function saveWorkbookPackages(packages, pythonPaths = []) {
    try {
        if (!isOfficeSettingsAvailable()) {
            window.logToServer('DEBUG', 'Office settings not available, cannot save packages');
            return false;
        }

        // Save packages
        if (Array.isArray(packages)) {
            const packagesJson = safeJsonStringify(packages, 'package list for persistence');
            Office.context.document.settings.set("XPyCode_Packages", packagesJson);
        }

        // Save python paths
        if (Array.isArray(pythonPaths)) {
            const pathsJson = safeJsonStringify(pythonPaths, 'python paths for persistence');
            Office.context.document.settings.set("XPyCode_PythonPaths", pathsJson);
        }
        Office.context.document.settings.saveAsync((asyncResult) => {
            if (asyncResult.status === Office.AsyncResultStatus.Failed) {
                window.logToServer('ERROR', 'Failed to save package list and python paths:', asyncResult.error.message);
            } else {
                window.logToServer('DEBUG', 'Successfully saved package list and python paths to workbook');
            }
        });
        return true;
    } catch (err) {
        window.logToServer('ERROR', 'Error saving package list and python paths:', err);
    }
    return false;
}

/**
 * Load package list from workbook settings
 * @returns {Array|null} List of package objects or null if not available
 */
export function loadWorkbookPackages() {
    try {
        if (!isOfficeSettingsAvailable()) {
            window.logToServer('DEBUG', 'Office settings not available, cannot load packages');
            return null;
        }
        
        const packagesJson = Office.context.document.settings.get("XPyCode_Packages");
        if (!packagesJson) {
            window.logToServer('DEBUG', 'No persisted packages found');
            return [];
        }
        
        const packages = safeJsonParse(packagesJson, 'package list');
        if (packages && Array.isArray(packages)) {
            window.logToServer('DEBUG', 'Loaded', packages.length, 'persisted packages');
            return packages;
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error loading package list:', err);
    }
    return null;
}

/**
 * Load python paths from workbook settings
 * @returns {Array|null} List of python path objects or null if not available
 */
export function loadWorkbookPythonPaths() {
    try {
        if (!isOfficeSettingsAvailable()) {
            window.logToServer('DEBUG', 'Office settings not available, cannot load python paths');
            return null;
        }
        
        const pathsJson = Office.context.document.settings.get("XPyCode_PythonPaths");
        if (!pathsJson) {
            window.logToServer('DEBUG', 'No persisted python paths found');
            return [];
        }
        
        const paths = safeJsonParse(pathsJson, 'python paths');
        if (paths && Array.isArray(paths)) {
            window.logToServer('DEBUG', 'Loaded', paths.length, 'persisted python paths');
            return paths;
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error loading python paths:', err);
    }
    return null;
}

/**
 * Sync persisted packages and python paths with server on startup
 * @param {Function} sendRaw - Function to send raw messages to server
 */
export function syncPackagesOnStartup(sendRaw) {
    try {
        const packages = loadWorkbookPackages();
        const pythonPaths = loadWorkbookPythonPaths();
        
        if ((packages && packages.length > 0) || (pythonPaths && pythonPaths.length > 0)) {
            window.logToServer('DEBUG', 'Syncing', packages?.length || 0, 'packages and', pythonPaths?.length || 0, 'python paths with server');
            
            sendRaw({
                type: 'client_sync_packages',
                packages: packages || [],
                python_paths: pythonPaths || []
            });
            
            window.logToServer('DEBUG', 'Sent client_sync_packages message to server');
        } else {
            window.logToServer('DEBUG', 'No persisted packages or python paths to sync');
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error syncing packages on startup:', err);
    }
}
