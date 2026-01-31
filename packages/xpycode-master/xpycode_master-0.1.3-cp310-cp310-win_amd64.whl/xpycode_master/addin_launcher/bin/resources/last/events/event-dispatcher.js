// XPyCode Event Dispatcher
// Manages Excel event subscriptions and dispatches events to Python backend

import { TEMPORARY_PARENT_ID } from '../core/constants.js';
import { getObjectByType } from '../utils/index.js';
import { getSetting } from '../settings/index.js'; 
/**
 * Event Dispatcher class
 * Handles registration of Excel event handlers and dispatches events to Python backend
 */
export class EventDispatcher {
    /**
     * @param {ContextManager} contextManager - The context manager for Excel operations
     * @param {Messaging} messaging - The messaging instance for sending events to Python
     */
    constructor(contextManager, messaging) {
        this.contextManager = contextManager;
        this.messaging = messaging;
        // Registry of active event handlers: Map<string, EventHandlerResult>
        // Key format: "ObjectId:EventName"
        this.activeHandlers = new Map();
    }

    /**
     * Apply event configuration. Clears existing listeners and registers new ones.
     * @param {Object} config - Event configuration in format: { "ObjectId": { "ObjectType": "...", "events": { "EventName": {"module_name": "...", "function_name": "..."} } } }
     */
    async applyConfig(config) {
        window.logToServer('DEBUG', '[EventDispatcher] Applying config:', config);

        // Step 1: Clear all existing listeners
        await this._clearAllHandlers();

        // Step 2: If no config or empty config, just return
        if (!config || Object.keys(config).length === 0) {
            window.logToServer('DEBUG', '[EventDispatcher] No event config to apply');
            return;
        }

        // Step 3: Register new listeners based on config
        await Excel.run(async (context) => {
            for (const [objectId, configData] of Object.entries(config)) {
                if (!configData || typeof configData !== 'object') {
                    window.logToServer('WARNING', `[EventDispatcher] Invalid events config for object "${objectId}"`);
                    continue;
                }

                // Check if this is new format (with ObjectType)
                const objectType = configData.ObjectType || configData.objectType;
                const events = configData.events || configData;

                if (objectType && events !== configData) {
                    // New ID-based format
                    for (const [eventName, handlerInfo] of Object.entries(events)) {
                        try {
                            // Check if handlerInfo is an object with split fields
                            let moduleName, functionName;
                            if (typeof handlerInfo === 'object' && handlerInfo.module_name && handlerInfo.function_name) {
                                // New format with split fields
                                moduleName = handlerInfo.module_name;
                                functionName = handlerInfo.function_name;
                            } else {
                                window.logToServer('WARNING', `[EventDispatcher] Invalid handler format for ${objectType}[${objectId}].${eventName}`);
                                continue;
                            }
                            
                            await this._registerHandler(context, objectType, objectId, eventName, moduleName, functionName);
                        } catch (err) {
                            window.logToServer('ERROR', `[EventDispatcher] Failed to register handler for ${objectType}[${objectId}].${eventName}:`, err);
                        }
                    }
                } else {
                    window.logToServer('WARNING', `[EventDispatcher] Skipping legacy format config for object "${objectId}"`);
                }
            }
            await context.sync();
        });

        window.logToServer('DEBUG', '[EventDispatcher] Config applied. Active handlers:', this.activeHandlers.size);
    }

    /**
     * Public API: Register a single event handler for an Excel object.
     * 
     * @param {string} objectType - The type of Excel object (e.g., "Worksheet", "Table")
     * @param {string} objectId - The ID of the Excel object
     * @param {string} eventName - The event name
     * @param {string} moduleName - The Python module name
     * @param {string} functionName - The Python function name
     */
    async registerHandler(objectType, objectId, eventName, moduleName, functionName) {
        await Excel.run(async (context) => {
            await this._registerHandler(context, objectType, objectId, eventName, moduleName, functionName);
        });
    }

    /**
     * Public API: Unregister a single event handler.
     * 
     * @param {string} objectId - The ID of the Excel object
     * @param {string} eventName - The event name
     */
    async unregisterHandler(objectId, eventName) {
        await this._unregisterHandler(objectId, eventName);
    }

    /**
     * Clear all active event handlers
     */
    async _clearAllHandlers() {
        if (this.activeHandlers.size === 0) {
            return;
        }

        window.logToServer('DEBUG', '[EventDispatcher] Clearing', this.activeHandlers.size, 'active handlers');

        await Excel.run(async (context) => {
            for (const [key, handlerResult] of this.activeHandlers.entries()) {
                try {
                    handlerResult.remove();
					await handlerResult.context.sync();
                    window.logToServer('DEBUG', `[EventDispatcher] Removed handler: ${key}`);
                } catch (err) {
                    window.logToServer('WARNING', `[EventDispatcher] Error removing handler ${key}:`, err);
                }
            }
            await context.sync();
        });

        this.activeHandlers.clear();
    }

    /**
     * Register an event handler for a specific object and event name
     * @param {Excel.RequestContext} context - The Excel context
     * @param {string} objectType - The type of the Excel object (e.g., "Worksheet", "Table", "Chart")
     * @param {string} objectId - The ID of the Excel object
     * @param {string} eventName - The event name (e.g., "onSelectionChanged", "onChanged")
     * @param {string} moduleName - The Python module name
     * @param {string} functionName - The Python function name
     */
    async _registerHandler(context, objectType, objectId, eventName, moduleName, functionName) {
        // Note: OfficeTools is a global from office_tools.js loaded via script tag in HTML
        // TODO: Convert office_tools.js to ES6 module and import it
        
        // Try to resolve using ID-based approach
        let object = null;
        try {
            object = await getObjectByType(context, objectType, objectId);
            if (!object) {
                window.logToServer('WARNING', `[EventDispatcher] Could not resolve object with type "${objectType}" and ID "${objectId}"`);
                return;
            }
        } catch (err) {
            window.logToServer('ERROR', `[EventDispatcher] Error resolving object:`, err);
            return;
        }

        // Use the eventName directly to access the event handler property
        const eventHandler = object[eventName];

        if (!eventHandler || typeof eventHandler.add !== 'function') {
            window.logToServer('WARNING', `[EventDispatcher] Event handler "${eventName}" not available on ${objectType}`);
            return;
        }

        // Create the callback function
        const callback = this._createEventCallback(objectId, eventName, moduleName, functionName, objectType);

		//Try to Unregister the previous onerror
		await this._unregisterHandler(objectId, eventName, true);

        // Register the event handler and store the result
        const handlerResult = eventHandler.add(callback);
        await context.sync();

        // Store the handler result for later removal using ID-based key
        const handlerKey = `${objectId}:${eventName}`;
        this.activeHandlers.set(handlerKey, handlerResult);

        window.logToServer('DEBUG', `[EventDispatcher] Registered handler for ${objectType}[${objectId}].${eventName} -> ${moduleName}.${functionName}`);
    }

    /**
     * Unregister an event handler for a specific object and event name
     * @param {string} objectId - The ID of the Excel object
     * @param {string} eventName - The event name
     */
    async _unregisterHandler(objectId, eventName, silent=false) {
        const handlerKey = `${objectId}:${eventName}`;
        const handlerResult = this.activeHandlers.get(handlerKey);
        
        if (!handlerResult) {
			if(!silent) {
				window.logToServer('WARNING', `[EventDispatcher] No handler found for ${objectId}:${eventName}`);
            }
			return;
        }

        await Excel.run(handlerResult.context, async (context) => {
            try {
                handlerResult.remove();
                await context.sync();
                this.activeHandlers.delete(handlerKey);
                window.logToServer('DEBUG', `[EventDispatcher] Unregistered handler for ${objectId}:${eventName}`);
            } catch (err) {
                window.logToServer('ERROR', `[EventDispatcher] Error unregistering handler:`, err);
            }
        });
    }

    /**
     * Create an event callback function that sends the event to Python
     * @param {string} objectName - The name or ID of the Excel object
     * @param {string} eventName - The event name
     * @param {string} moduleName - The Python module name
     * @param {string} functionName - The Python function name
     * @param {string} objectType - The type of the object (Worksheet, Table, etc.)
     * @returns {Function} - The callback function
     */
    _createEventCallback(objectName, eventName, moduleName, functionName, objectType) {
        const messaging = this.messaging;
        const contextManager = this.contextManager;

        return async (eventArgs) => {
            try {
                // Check if editor events are enabled
                if (!getSetting('enableEditorEvents')) {
                    window.logToServer('DEBUG', `[EventDispatcher] Event suppressed (events disabled): ${objectName}.${eventName}`);
                    return;
                }
            
                window.logToServer('DEBUG', `[EventDispatcher] Event fired: ${objectName}.${eventName}`, eventArgs);

                // Serialize eventArgs directly using toWire with TEMPORARY_PARENT_ID
                // This allows tracking of event objects without a full object model path
                const serializedArgs = contextManager.toWire(eventArgs, TEMPORARY_PARENT_ID, 'eventArgs');

                // Construct the payload with split module_name and function_name
                const payload = {
                    type: 'event_execution',
                    module_name: moduleName,
                    function_name: functionName,
                    object_name: objectName,
                    event_name: eventName,
                    object_type: objectType,
                    args: [serializedArgs]
                };

                // Send to Python backend
                messaging.sendRaw(payload);
                window.logToServer('DEBUG', `[EventDispatcher] Sent event to Python:`, payload);
            } catch (err) {
                window.logToServer('ERROR', `[EventDispatcher] Failed to send event to Python:`, err);
            }
        };
    }
}
