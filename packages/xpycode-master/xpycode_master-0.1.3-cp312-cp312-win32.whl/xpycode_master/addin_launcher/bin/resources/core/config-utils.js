/**
 * Configuration Utilities
 * 
 * Utilities for loading and managing configuration.
 * 
 * IMPORTANT: This file is in core/ and MUST maintain retrocompatibility.
 * Any changes must be backward compatible with older versions.
 */

/**
 * Watchdog ports to scan when running in external addin mode.
 * IMPORTANT: Keep in sync with WATCHDOG_PORTS in xpycode_master/config.py
 */
const WATCHDOG_PORTS = [51171, 51172, 51173, 51174, 51175, 51176, 51177, 51178, 51179];

// Key for storing discovered watchdog port in localStorage
const WATCHDOG_PORT_STORAGE_KEY = 'xpycode_discovered_watchdog_port';

/**
 * Reload config from server. Handles both local and external addin modes.
 * 
 * Local mode: Fetches /config.json from local server
 * External mode: Scans for local watchdog and fetches config from /ports endpoint
 */
export async function reloadConfig() {
	try {
		// First, try to fetch config.json
		const res = await fetch('./config.json', { cache: 'no-store' });
		const config = await res.json();

		// Check if we're in external addin mode (watchdogPort === -1)
		if (config.watchdogPort === -1) {
			// External mode: need to discover local watchdog
			const watchdogConfig = await discoverWatchdogAndGetConfig();
			if (watchdogConfig) {
				window.XPYCODE_CONFIG = watchdogConfig;
				return;
			}
			// If discovery failed, use config as-is (will have -1 values)
		}

		window.XPYCODE_CONFIG = config;
	} catch (e) {
		window.logToServer('ERROR','[XPyCode] Error loading config:', e);
	}
}

/**
 * Discover local watchdog by scanning ports and fetch config from /ports endpoint.
 * Caches discovered port for faster subsequent lookups.
 * 
 * @returns {Object|null} Config object or null if discovery failed
 */
async function discoverWatchdogAndGetConfig() {
	// Try cached port first
	const cachedPort = localStorage.getItem(WATCHDOG_PORT_STORAGE_KEY);
	if (cachedPort) {
		const port = parseInt(cachedPort, 10);
		const config = await tryWatchdogPort(port);
		if (config) {
			return config;
		}
		// Cached port no longer valid, clear it
		localStorage.removeItem(WATCHDOG_PORT_STORAGE_KEY);
	}

	// Scan all watchdog ports
	for (const port of WATCHDOG_PORTS) {
		const config = await tryWatchdogPort(port);
		if (config) {
			// Cache the discovered port
			localStorage.setItem(WATCHDOG_PORT_STORAGE_KEY, port.toString());
			return config;
		}
	}

	window.logToServer('WARNING','[XPyCode] Could not discover local watchdog on any port');
	return null;
}

/**
 * Try to connect to watchdog on a specific port.
 * Validates it's actually XPyCode watchdog via /health endpoint.
 * If valid, fetches config from /ports endpoint.
 * 
 * @param {number} port - Port to try
 * @returns {Object|null} Config object or null if failed
 */
async function tryWatchdogPort(port) {
	try {
		// First validate with /health endpoint
		const healthUrl = `http://localhost:${port}/health`;
		const healthRes = await fetch(healthUrl, {
			cache: 'no-store',
			signal: AbortSignal.timeout(1000) // 2 second timeout
		});

		//if (!healthRes.ok) return null;

		const health = await healthRes.json();

		// Verify this is XPyCode watchdog (check for expected fields)
		if (health.status !== 'ok' || health.app !== 'xpycode_watchdog' || typeof health.watchdog_port !== 'number') {
			return null;
		}

		// Now fetch full config from /ports endpoint
		const portsUrl = `http://localhost:${port}/ports`;
		const portsRes = await fetch(portsUrl, { cache: 'no-store' });

		//if (!portsRes.ok) return null;

		const ports = await portsRes.json();
		// Build config object matching expected format
		return {
			serverPort: ports.server_port,
			watchdogPort: ports.watchdog_port,
			authToken: ports.auth_token,
			docsPort: ports.docs_port,
			loggingLevel: health.logging_level || 'INFO'
		};
	} catch (e) {
		// Connection failed, timeout, etc. - this port doesn't have watchdog
		return null;
	}
}

