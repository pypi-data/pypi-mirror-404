/**
 * XPyCode Taskpane Entry Point
 * 
 * Minimal loader that detects the XPyCode version and dynamically loads
 * the appropriate versioned modules.
 * 
 * This file should remain minimal and stable. All application logic
 * is in the versioned modules (last/ or version-specific folders).
 */

import { loadVersionedApp } from './core/loader.js';

// Wait for Office.js to be ready
Office.onReady(async (info) => {
    console.log('[XPyCode] Office.onReady - Host:', info.host, 'Platform:', info.platform);
    
    // Load the versioned application
    await loadVersionedApp();
});
