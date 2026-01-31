// XPyCode Event Configuration Storage
// Handles persistence of event configuration using Custom XML Parts in the workbook

/**
 * Get the XPyCode events namespace for Custom XML Parts
 * @returns {string} Namespace URI
 */
export function getEventsNamespace() {
    return 'http://xpycode.local/events';
}

/**
 * Get event configuration from the workbook.
 * @returns {Promise<Object|null>} Event mapping JSON object or null if not found
 */
export async function getEventConfigFromWorkbook() {
    return Excel.run(async (context) => {
        const xmlParts = context.workbook.customXmlParts;
        const eventsNs = getEventsNamespace();
        const matchingParts = xmlParts.getByNamespace(eventsNs);
        matchingParts.load('items');
        await context.sync();

        for (const part of matchingParts.items) {
            const xmlBlob = part.getXml();
            await context.sync();
            
            // Parse the XML to extract event config
            const parser = new DOMParser();
            const doc = parser.parseFromString(xmlBlob.value, 'text/xml');
            const configEl = doc.documentElement;
            if (configEl && configEl.localName === 'eventConfig') {
                const configJson = configEl.textContent || '{}';
                try {
                    const returnConfig = JSON.parse(configJson);
					window.logToServer('DEBUG', `I've retreive ${Object.keys(returnConfig).length} events.`);
					return returnConfig;
                } catch (e) {
                    window.logToServer('ERROR', 'Error parsing event config JSON:', e);
                    return {};
                }
            }
        }
        return {};
    });
}

/**
 * Save event configuration to the workbook.
 * If configuration already exists, it is replaced.
 * @param {Object} config - Event configuration object
 * @returns {Promise<void>}
 */
export async function saveEventConfigToWorkbook(config) {
    return Excel.run(async (context) => {
        const xmlParts = context.workbook.customXmlParts;
        const eventsNs = getEventsNamespace();
        
        // First, delete any existing event config
        const matchingParts = xmlParts.getByNamespace(eventsNs);
        matchingParts.load('items');
        await context.sync();

        for (const part of matchingParts.items) {
            part.delete();
        }
        await context.sync();

        // Create new XML for the event config
        const configJson = JSON.stringify(config);
        // Escape special XML characters in the JSON string
        const escapedConfig = configJson
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        const xml = `<?xml version="1.0" encoding="UTF-8"?>
<eventConfig xmlns="${eventsNs}">${escapedConfig}</eventConfig>`;
        
        xmlParts.add(xml);
        await context.sync();
        
        window.logToServer('DEBUG', `Event config saved to workbook. Size is ${Object.keys(config).length}`);
    });
}
