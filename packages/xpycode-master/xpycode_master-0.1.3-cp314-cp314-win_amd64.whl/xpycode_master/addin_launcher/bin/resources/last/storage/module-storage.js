// XPyCode Module Storage
// Handles persistence of Python modules using Custom XML Parts in the workbook

/**
 * Get the XPyCode namespace for Custom XML Parts
 * @returns {string} Namespace URI
 */
export function getXPyCodeNamespace() {
    return 'http://xpycode.local/modules';
}

/**
 * Get all modules stored in the workbook.
 * @returns {Promise<Object>} Object mapping module names to code
 */
export async function getModulesFromWorkbook() {
    return Excel.run(async (context) => {
        const xmlParts = context.workbook.customXmlParts;
        const xpycodeNs = getXPyCodeNamespace();
        const matchingParts = xmlParts.getByNamespace(xpycodeNs);
        matchingParts.load('items');
        await context.sync();

        const modules = {};
        for (const part of matchingParts.items) {
            const xmlBlob = part.getXml();
            await context.sync();
            
            // Parse the XML to extract module name and code
            const parser = new DOMParser();
            const doc = parser.parseFromString(xmlBlob.value, 'text/xml');
            const moduleEl = doc.documentElement;
            if (moduleEl && moduleEl.localName === 'module') {
                const name = moduleEl.getAttribute('name');
                const code = moduleEl.textContent || '';
                if (name) {
                    modules[name] = code;
                }
            }
        }
        return modules;
    });
}

/**
 * Save a module to the workbook.
 * If the module already exists, it is updated.
 * @param {string} moduleName - Name of the module
 * @param {string} code - Module code
 * @returns {Promise<void>}
 */
export async function saveModuleToWorkbook(moduleName, code) {
    return Excel.run(async (context) => {
        const xmlParts = context.workbook.customXmlParts;
        const xpycodeNs = getXPyCodeNamespace();
        
        // First, try to find and delete existing module with same name
        const matchingParts = xmlParts.getByNamespace(xpycodeNs);
        matchingParts.load('items');
        await context.sync();

        for (const part of matchingParts.items) {
            const xmlBlob = part.getXml();
            await context.sync();
            
            const parser = new DOMParser();
            const doc = parser.parseFromString(xmlBlob.value, 'text/xml');
            const moduleEl = doc.documentElement;
            if (moduleEl && moduleEl.getAttribute('name') === moduleName) {
                part.delete();
                await context.sync();
                break;
            }
        }

        // Create new XML for the module
        // Escape special XML characters in code
        const escapedCode = code
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Escape special XML characters in module name for attribute
        const escapedModuleName = moduleName
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&apos;');
        
        const xml = `<?xml version="1.0" encoding="UTF-8"?>
<module xmlns="${xpycodeNs}" name="${escapedModuleName}">${escapedCode}</module>`;
        
        xmlParts.add(xml);
        await context.sync();
        
        window.logToServer('DEBUG', 'Module saved to workbook:', moduleName);
    });
}

/**
 * Load a specific module from the workbook.
 * @param {string} moduleName - Name of the module to load
 * @returns {Promise<string|null>} Module code or null if not found
 */
export async function loadModuleFromWorkbook(moduleName) {
    return Excel.run(async (context) => {
        const xmlParts = context.workbook.customXmlParts;
        const xpycodeNs = getXPyCodeNamespace();
        const matchingParts = xmlParts.getByNamespace(xpycodeNs);
        matchingParts.load('items');
        await context.sync();

        for (const part of matchingParts.items) {
            const xmlBlob = part.getXml();
            await context.sync();
            
            const parser = new DOMParser();
            const doc = parser.parseFromString(xmlBlob.value, 'text/xml');
            const moduleEl = doc.documentElement;
            if (moduleEl && moduleEl.getAttribute('name') === moduleName) {
                return moduleEl.textContent || '';
            }
        }
        return null;
    });
}

/**
 * Delete a module from the workbook.
 * @param {string} moduleName - Name of the module to delete
 * @returns {Promise<void>}
 */
export async function deleteModuleFromWorkbook(moduleName) {
    return Excel.run(async (context) => {
        const xmlParts = context.workbook.customXmlParts;
        const xpycodeNs = getXPyCodeNamespace();
        const matchingParts = xmlParts.getByNamespace(xpycodeNs);
        matchingParts.load('items');
        await context.sync();

        for (const part of matchingParts.items) {
            const xmlBlob = part.getXml();
            await context.sync();
            
            const parser = new DOMParser();
            const doc = parser.parseFromString(xmlBlob.value, 'text/xml');
            const moduleEl = doc.documentElement;
            if (moduleEl && moduleEl.getAttribute('name') === moduleName) {
                part.delete();
                await context.sync();
                window.logToServer('DEBUG', 'Module deleted from workbook:', moduleName);
                return;
            }
        }
        window.logToServer('DEBUG', 'Module not found in workbook:', moduleName);
    });
}
