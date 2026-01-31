/**
 * Version Detector
 * 
 * Discovers the local XPyCode watchdog and retrieves version information.
 * 
 * IMPORTANT: This file is in core/ and MUST maintain retrocompatibility.
 * Any changes must be backward compatible with older versions.
 */

// Watchdog ports to scan - KEEP IN SYNC with xpycode_master/config.py WATCHDOG_PORTS
const WATCHDOG_PORTS = [51171, 51172, 51173, 51174, 51175, 51176, 51177, 51178, 51179];

// Storage key for caching discovered port
const WATCHDOG_PORT_STORAGE_KEY = 'xpycode_watchdog_port';

/**
 * Try to connect to watchdog on a specific port
 * @param {number} port - Port to try
 * @returns {Promise<Object|null>} - Watchdog info or null if not found
 */
async function tryWatchdogPort(port) {
    try {
        const healthUrl = `http://localhost:${port}/health`;
        const response = await fetch(healthUrl, {
            cache: 'no-store',
            signal: AbortSignal.timeout(2000)
        });
        
        if (!response.ok) return null;
        
        const health = await response.json();
        
        // Verify this is XPyCode watchdog
        if (health.status !== 'ok' || health.app !== 'xpycode_watchdog') {
            return null;
        }
        
        return {
            port: port,
            version: health.version || '0.1.0',
            ...health
        };
    } catch (e) {
        return null;
    }
}

/**
 * Discover the XPyCode watchdog
 * @returns {Promise<Object|null>} - Watchdog info or null if not found
 */
export async function discoverWatchdog() {
    // Try cached port first
    const cachedPort = localStorage.getItem(WATCHDOG_PORT_STORAGE_KEY);
    if (cachedPort) {
        const port = parseInt(cachedPort, 10);
        const result = await tryWatchdogPort(port);
        if (result) {
            return result;
        }
        // Cached port invalid, clear it
        localStorage.removeItem(WATCHDOG_PORT_STORAGE_KEY);
    }
    
    // Scan all ports
    for (const port of WATCHDOG_PORTS) {
        const result = await tryWatchdogPort(port);
        if (result) {
            // Cache the discovered port
            localStorage.setItem(WATCHDOG_PORT_STORAGE_KEY, port.toString());
            return result;
        }
    }
    
    return null;
}

/**
 * Normalize version string
 * - "0.1.0" → "0.1.0" (dev version, maps to "last")
 * - "0.1.5.dev1" → "0.1.5"
 * - "0.1.5-beta" → "0.1.5"
 * - "0.1.5" → "0.1.5"
 * 
 * @param {string} version - Raw version string
 * @returns {string} - Normalized version (X.Y.Z format)
 */
export function normalizeVersion(version) {
    if (!version) return '0.1.0';
    
    // Extract major.minor.patch
    const match = version.match(/^(\d+\.\d+\.\d+)/);
    return match ? match[1] : version;
}

/**
 * Get the base path for loading versioned modules
 * - "0.1.0" → "last" (development version)
 * - "0.1.5" → "0.1.5" (released version)
 * 
 * @param {string} version - Normalized version string
 * @returns {string} - Base path for imports
 */
export function getVersionBasePath(version) {
    if (version === '0.1.0') {
        return 'last';
    }
    return version;
}
