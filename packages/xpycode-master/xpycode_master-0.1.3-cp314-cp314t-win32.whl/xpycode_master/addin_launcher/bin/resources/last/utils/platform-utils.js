/**
 * Platform detection and safe API execution utilities
 */

export function getPlatformInfo() {
    return {
        isOnline: Office.context.platform === Office.PlatformType.OfficeOnline,
        isWindows: Office.context.platform === Office.PlatformType.PC,
        isMac: Office.context.platform === Office.PlatformType.Mac,
        host: Office.context.host
    };
}

/**
 * Safely execute an Excel API operation with fallback
 * @param {Function} operation - Async function to execute
 * @param {any} fallbackValue - Value to return if operation fails
 * @param {string} operationName - Name for logging
 */
export async function safeExcelOperation(operation, fallbackValue = null, operationName = "operation") {
    try {
        return await operation();
    } catch (e) {
        if (e.message && e.message.includes("not implemented")) {
            console.warn(`[XPyCode] ${operationName} not supported on this platform`);
        } else {
            console.error(`[XPyCode] ${operationName} failed: `, e);
        }
        return fallbackValue;
    }
}

/**
 * Get list of unsupported features for current platform
 */
export function getUnsupportedFeatures() {
    const unsupported = [];
    const platform = getPlatformInfo();

    if (platform.isOnline) {
        // Known limitations in Excel Online
        unsupported.push('shapes');
        unsupported.push('linkedEntityDataDomains');
        unsupported.push('someCustomFunctions'); // if applicable
    }

    return unsupported;
}