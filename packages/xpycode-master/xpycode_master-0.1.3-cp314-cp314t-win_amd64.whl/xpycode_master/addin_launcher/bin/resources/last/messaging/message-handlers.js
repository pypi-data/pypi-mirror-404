// XPyCode Message Handlers
// Maps message types to their handler functions

import { getModulesFromWorkbook, saveModuleToWorkbook, loadModuleFromWorkbook, deleteModuleFromWorkbook } from '../storage/module-storage.js';
import { getEventConfigFromWorkbook, saveEventConfigToWorkbook } from '../storage/event-config-storage.js';
import { saveWorkbookPackages, loadWorkbookPackages, loadWorkbookPythonPaths, isOfficeSettingsAvailable, safeJsonParse } from '../storage/package-storage.js';
import { handleFunctionResult } from '../udf/udf-dispatcher.js';
import { handleStreamingResult } from '../udf/streaming-handler.js';
import { showMessageBox as showMessageBoxDialog } from '../ui/message-box/index.js';
import { setSetting, saveSettings } from '../settings/index.js';
import {
    CONSOLE_CHECK_INTERVAL,
    CONSOLE_MAX_CHARS,
    CONSOLE_MAX_LINES,
    CONSOLE_TRIM_TO_LINES
} from '../core/constants.js';
import { getEventsDictionary, getWorkbookTree } from '../utils/index.js'; 

/**
 * Handle chunk messages for reassembly
 */
export function handleChunk(env, chunkHandler, onMessageCallback) {
    const reassembled = chunkHandler.handleChunk(env);
    if (reassembled) {
        // Process the reassembled message by calling _onMessage again
        onMessageCallback({ data: JSON.stringify(reassembled) });
    }
}

/**
 * Handle Excel request from kernel (via Business Layer)
 */
export async function handleExcelRequest(env, contextManager, sendRaw) {
    const payload = env.payload || {};
    window.logToServer('DEBUG', 'Processing excel_request:', payload.method, payload.name, 'caller:', payload.caller);
    let resp;
    try {
        resp = await contextManager.processMessage(payload);
    } catch (err) {
        window.logToServer('ERROR', 'Error processing excel_request:', err);
        resp = { ok: false, error: { message: String(err.message || err) } };
    }
    // Send response back through Business Layer
    const responsePayload = { ...resp, requestId: payload.requestId, kind: 'response' };
    window.logToServer('DEBUG', 'Sending excel_response:', resp.ok ? 'success' : 'error', responsePayload);
    sendRaw({
        type: 'excel_response',
        payload: responsePayload
    });
}

/**
 * Handle sys_request (synchronous COM-like calls from Python to Excel)
 */
export async function handleSysRequest(env, contextManager, sendRaw) {
    const payload = env.payload || {};
    window.logToServer('DEBUG', 'Processing sys_request:', payload.method, payload.name, 'caller:', payload.caller);
    let resp;
    try {
        resp = await contextManager.processMessage(payload);
    } catch (err) {
        window.logToServer('ERROR', 'Error processing sys_request:', err);
        resp = { ok: false, error: { message: String(err.message || err) } };
    }
    // Send response back through Business Layer as sys_response
    const responsePayload = { ...resp, requestId: payload.requestId, kind: 'response' };
    window.logToServer('DEBUG', 'Sending sys_response:', resp.ok ? 'success' : 'error', responsePayload);
    sendRaw({
        type: 'sys_response',
        payload: responsePayload
    });
}

/**
 * Handle stdout from Python kernel
 */
export function handleStdout(env, consoleAppendCount, currentSettings) {
    const source = env.source || 'addin';  // Default to 'addin' for backwards compatibility
    if (source!='addin') return consoleAppendCount;
    let content = env.content || '';

    const timestamp = new Date().toLocaleTimeString();
    content = content.split('\n').map(line => line && line != '' ? ('[' + timestamp + '] ' + line) : line).join('\n');
    window.logToServer('DEBUG', `[XPyCode stdout]`, content);
    
    try {
        // Display in taskpane console-output element
        const consoleOutput = document.getElementById('console-output');
        if (consoleOutput) {
            // Create a span element for normal text (consistent with stderr approach)
            const span = document.createElement('span');
            span.textContent = content;
            consoleOutput.appendChild(span);
            
            // Limit console output to prevent memory issues
            // Check and trim periodically based on configured interval
            consoleAppendCount++;
            
            if (consoleAppendCount % CONSOLE_CHECK_INTERVAL === 0) {
                // Use character length as proxy to avoid expensive split on every check
                if (consoleOutput.textContent.length > CONSOLE_MAX_CHARS) {
                    // Count newlines efficiently before doing expensive split
                    const newlineMatches = consoleOutput.textContent.match(/\n/g);
                    const lineCount = newlineMatches ? newlineMatches.length + 1 : 1;
                    
                    if (lineCount > CONSOLE_MAX_LINES) {
                        // Keep only the most recent lines
                        // Note: This replaces DOM with plain text, losing span styling
                        // This is acceptable for performance when trimming very large output
                        const lines = consoleOutput.textContent.split('\n');
                        consoleOutput.textContent = '';
                        consoleOutput.insertAdjacentText('beforeend', lines.slice(-CONSOLE_TRIM_TO_LINES).join('\n'));
                    }
                }
            }
            
            // Scroll to bottom to show latest output if autoscroll is enabled
            if (currentSettings.autoscroll) {
                consoleOutput.scrollTop = consoleOutput.scrollHeight;
            }
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error updating console for stdout:', err);
    }
    return consoleAppendCount;
}

/**
 * Handle stderr from Python kernel
 */
export function handleStderr(env, consoleAppendCount, currentSettings, showErrorNotification) {
    const source = env.source || 'addin';  // Default to 'addin' for backwards compatibility
    if (source!='addin') return consoleAppendCount;
    let content = env.content || '';
    const timestamp = new Date().toLocaleTimeString();
    content = content.split('\n').map(line => line && line !='' ? ('[' + timestamp + '] ' + line) : line).join('\n');
    window.logToServer('DEBUG', `[XPyCode stderr]`, content);
    
    // Show error notification when stderr is received
    showErrorNotification(content);


    
    try {
        // Display in taskpane console-output element with red color
        const consoleOutput = document.getElementById('console-output');
        if (consoleOutput) {
            // Create a span element for red text
            const span = document.createElement('span');
            span.style.color = 'red';
            span.textContent = content;
            consoleOutput.appendChild(span);
            
            // Limit console output to prevent memory issues
            // Check and trim periodically based on configured interval
            consoleAppendCount++;
            
            if (consoleAppendCount % CONSOLE_CHECK_INTERVAL === 0) {
                // Use character length as proxy to avoid expensive split on every check
                if (consoleOutput.textContent.length > CONSOLE_MAX_CHARS) {
                    // Count newlines efficiently before doing expensive split
                    const newlineMatches = consoleOutput.textContent.match(/\n/g);
                    const lineCount = newlineMatches ? newlineMatches.length + 1 : 1;
                    
                    if (lineCount > CONSOLE_MAX_LINES) {
                        // Keep only the most recent lines
                        // Note: This replaces DOM with plain text, losing span styling
                        // This is acceptable for performance when trimming very large output
                        const lines = consoleOutput.textContent.split('\n');
                        consoleOutput.textContent = '';
                        consoleOutput.insertAdjacentText('beforeend', lines.slice(-CONSOLE_TRIM_TO_LINES).join('\n'));
                    }
                }
            }
            
            // Scroll to bottom to show latest output if autoscroll is enabled
            if (currentSettings.autoscroll) {
                consoleOutput.scrollTop = consoleOutput.scrollHeight;
            }
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error updating console for stderr:', err);
    }
    return consoleAppendCount;
}

/**
 * Handle get_modules_request
 */
export async function handleGetModulesRequest(env, sendRaw) {
    window.logToServer('DEBUG', 'Processing get_modules_request');
    try {
        const modules = await getModulesFromWorkbook();
        sendRaw({
            type: 'get_modules_response',
            modules: modules,
            requestId: env.requestId
        });
    } catch (err) {
        window.logToServer('ERROR', 'Error getting modules:', err);
        sendRaw({
            type: 'get_modules_response',
            modules: {},
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}

/**
 * Handle get_functions_request
 */
export async function handleGetFunctionsRequest(env, sendRaw) {
    window.logToServer('DEBUG', 'Processing get_functions_request');
    try {
        // Get functions from Office settings (same logic as client_sync_functions)
        let functions = [];
        
        if (isOfficeSettingsAvailable()) {
            const savedFunctionsJson = Office.context.document.settings.get("XPyCode_Functions");
            if (savedFunctionsJson) {
                const parsedFunctions = safeJsonParse(savedFunctionsJson, 'saved function metadata');
                if (parsedFunctions && Array.isArray(parsedFunctions)) {
                    functions = parsedFunctions;
                }
            }
        }
        
        sendRaw({
            type: 'get_functions_response',
            functions: functions,
            requestId: env.requestId
        });
        
        window.logToServer('DEBUG', `Sent ${functions.length} functions for get_functions_request`);
    } catch (err) {
        window.logToServer('ERROR', 'Error handling get_functions_request:', err);
        sendRaw({
            type: 'get_functions_response',
            functions: [],
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}

/**
 * Handle get_packages_request
 */
export async function handleGetPackagesRequest(env, sendRaw) {
    window.logToServer('DEBUG', 'Processing get_packages_request');
    try {
        // Get packages from Office settings (same logic as client_sync_packages)
        const packages = loadWorkbookPackages() || [];
        const pythonPaths = loadWorkbookPythonPaths() || [];
        
        sendRaw({
            type: 'get_packages_response',
            packages: packages,
            python_paths: pythonPaths,
            requestId: env.requestId
        });
        
        window.logToServer('DEBUG', `Sent ${packages.length} packages and ${pythonPaths.length} python paths for get_packages_request`);
    } catch (err) {
        window.logToServer('ERROR', 'Error handling get_packages_request:', err);
        sendRaw({
            type: 'get_packages_response',
            packages: [],
            python_paths: [],
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}


/**
 * Handle get_events_request
 */
export async function handleGetEventsRequest(env, sendRaw) {
    window.logToServer('DEBUG', 'Processing get_events_request');
    try {
        // Get packages from Office settings (same logic as client_sync_packages)
        const events_registered = await getEventConfigFromWorkbook();
        
        const events_tree = await Excel.run(async (context) => {
            // Use office_tools to get the full workbook tree with ID tracking
            const tree = await getWorkbookTree(context);
            return tree;
        });
        const events_definition = getEventsDictionary()

        sendRaw({
            type: 'get_events_response',
            events_registered: events_registered,
            events_tree: events_tree,
            events_definition: events_definition,
            requestId: env.requestId
        });

        window.logToServer('DEBUG', `Sent ${Object.keys(events_registered).length} events_registered and ${Object.keys(events_tree).length} events_tree and ${Object.keys(events_definition).length} events_definition for get_events_request`);
    } catch (err) {
        window.logToServer('ERROR', 'Error handling get_events_request:', err);
        sendRaw({
            type: 'get_events_request',
            events_registered: {},
            events_tree: {},
            events_definition: {},
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}


/**
 * Handle save_module_request
 */
export async function handleSaveModuleRequest(env, sendRaw) {
    const moduleName = env.module_name;
    const code = env.code || '';
    window.logToServer('DEBUG', 'Processing save_module_request for:', moduleName);
    try {
        await saveModuleToWorkbook(moduleName, code);
        sendRaw({
            type: 'save_module_response',
            module_name: moduleName,
            success: true,
            requestId: env.requestId
        });
    } catch (err) {
        window.logToServer('ERROR', 'Error saving module:', err);
        sendRaw({
            type: 'save_module_response',
            module_name: moduleName,
            success: false,
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}

/**
 * Handle load_module_request
 */
export async function handleLoadModuleRequest(env, sendRaw) {
    const moduleName = env.module_name;
    window.logToServer('DEBUG', 'Processing load_module_request for:', moduleName);
    try {
        const code = await loadModuleFromWorkbook(moduleName);
        sendRaw({
            type: 'load_module_response',
            module_name: moduleName,
            code: code,
            requestId: env.requestId
        });
    } catch (err) {
        window.logToServer('ERROR', 'Error loading module:', err);
        sendRaw({
            type: 'load_module_response',
            module_name: moduleName,
            code: null,
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}

/**
 * Handle delete_module_request
 */
export async function handleDeleteModuleRequest(env, sendRaw) {
    const moduleName = env.module_name;
    window.logToServer('DEBUG', 'Processing delete_module_request for:', moduleName);
    try {
        await deleteModuleFromWorkbook(moduleName);
        sendRaw({
            type: 'delete_module_response',
            module_name: moduleName,
            success: true,
            requestId: env.requestId
        });
    } catch (err) {
        window.logToServer('ERROR', 'Error deleting module:', err);
        sendRaw({
            type: 'delete_module_response',
            module_name: moduleName,
            success: false,
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}

/**
 * Handle get_event_config_request
 */
export async function handleGetEventConfigRequest(env, sendRaw, eventDispatcher) {
    window.logToServer('DEBUG', 'Processing get_event_config_request');
    try {
        const config = await getEventConfigFromWorkbook();
        
        // Apply event config using EventDispatcher if available
        if (eventDispatcher && config) {
            try {
                await eventDispatcher.applyConfig(config);
            } catch (dispatchErr) {
                window.logToServer('ERROR', 'Error applying event config to dispatcher:', dispatchErr);
            }
        }
        
        sendRaw({
            type: 'get_event_config_response',
            config: config,
            success: true,
            requestId: env.requestId
        });
    } catch (err) {
        window.logToServer('ERROR', 'Error getting event config:', err);
        sendRaw({
            type: 'get_event_config_response',
            config: null,
            success: false,
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}

/**
 * Handle save_event_config_request
 */
export async function handleSaveEventConfigRequest(env, sendRaw, eventDispatcher) {
    const config = env.config || {};
	const doSave = env.save || true;
    window.logToServer('DEBUG', `Processing save_event_config_request. Nb events ${Object.keys(config).length}`);
    try {
		if(doSave){
			await saveEventConfigToWorkbook(config);
        }
        // Refresh event listeners using EventDispatcher
        if (eventDispatcher) {
            try {
                await eventDispatcher.applyConfig(config);
            } catch (dispatchErr) {
                window.logToServer('ERROR', 'Error refreshing event listeners:', dispatchErr);
            }
        }
        
        sendRaw({
            type: 'save_event_config_response',
            success: true,
            requestId: env.requestId
        });
    } catch (err) {
        window.logToServer('ERROR', 'Error saving event config:', err);
        sendRaw({
            type: 'save_event_config_response',
            success: false,
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}

/**
 * Handle register_handler_request
 */
export async function handleRegisterHandlerRequest(env, sendRaw, registerEventHandlerFn) {
    const { object_type, object_id, event_name, module_name, function_name } = env;
    window.logToServer('DEBUG', 'Processing register_handler_request:', object_type, object_id, event_name);
    try {
        await registerEventHandlerFn(object_type, object_id, event_name, module_name, function_name);
        sendRaw({
            type: 'register_handler_response',
            object_type: object_type,
            object_id: object_id,
            event_name: event_name,
            success: true,
            requestId: env.requestId
        });
    } catch (err) {
        window.logToServer('ERROR', 'Error registering handler:', err);
        sendRaw({
            type: 'register_handler_response',
            object_type: object_type,
            object_id: object_id,
            event_name: event_name,
            success: false,
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}

/**
 * Handle unregister_handler_request
 */
export async function handleUnregisterHandlerRequest(env, sendRaw, unregisterEventHandlerFn) {
    const { object_id, event_name } = env;
    window.logToServer('DEBUG', 'Processing unregister_handler_request:', object_id, event_name);
    try {
        await unregisterEventHandlerFn(object_id, event_name);
        sendRaw({
            type: 'unregister_handler_response',
            object_id: object_id,
            event_name: event_name,
            success: true,
            requestId: env.requestId
        });
    } catch (err) {
        window.logToServer('ERROR', 'Error unregistering handler:', err);
        sendRaw({
            type: 'unregister_handler_response',
            object_id: object_id,
            event_name: event_name,
            success: false,
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}

/**
 * Handle scan_objects_request
 */
export async function handleScanObjectsRequest(env, sendRaw, scanWorkbookObjectsFn) {
    window.logToServer('DEBUG', 'Processing scan_objects_request');
    try {
        const objects = await scanWorkbookObjectsFn();
        sendRaw({
            type: 'scan_objects_response',
            objects: objects,
            success: true,
            requestId: env.requestId
        });
    } catch (err) {
        window.logToServer('ERROR', 'Error scanning workbook objects:', err);
        sendRaw({
            type: 'scan_objects_response',
            objects: null,
            success: false,
            error: String(err.message || err),
            requestId: env.requestId
        });
    }
}

/**
 * Handle sync_custom_functions message from Business Layer
 */
export function handleSyncCustomFunctions(env, registerDynamicFunctionsFn, storeFunctions) {
    const functions = env.functions || [];
    window.logToServer('DEBUG', 'Received sync_custom_functions:', functions);
    // Store the functions list
    storeFunctions(functions);
    window.logToServer('DEBUG', 'Custom functions stored:', functions.length, 'functions');
    // Register the functions dynamically with Excel
    registerDynamicFunctionsFn(functions);
}

/**
 * Handle batch_results message from Business Layer
 */
export function handleBatchResults(env, handleFunctionResultFn) {
    // Handle batched function results
    const results = env.results || [];
    window.logToServer('DEBUG', 'Received batch_results with', results.length, 'results');
    
    // Process each result synchronously
    results.forEach(result => handleFunctionResultFn(result));
}

/**
 * Handle batch message from Business Layer
 */
export async function handleBatch(env, processMessageFn) {
    // Handle generic batch messages
    const messages = env.messages || [];
    window.logToServer('DEBUG', 'Received batch with', messages.length, 'messages');
    
    // Process each message
    for (const msg of messages) {
        await processMessageFn(msg);
    }
}

/**
 * Handle function_execution_result message from Business Layer
 */
export function handleFunctionExecutionResult(env, pendingFunctionRequests, contextManager) {
    handleFunctionResult(env, pendingFunctionRequests, contextManager);
}

/**
 * Handle streaming_function_result message from Business Layer
 */
export function handleStreamingFunctionResult(env, streamingInvocations, contextManager) {
    handleStreamingResult(env, streamingInvocations, contextManager);
}

/**
 * Handle save_workbook_packages message from Business Layer
 */
export function handleSaveWorkbookPackages(env) {
    const packages = env.packages || null;
    const pythonPaths = env.python_paths || null;
    window.logToServer('DEBUG', 'Received save_workbook_packages:',  packages?.length, 'packages and', pythonPaths?.length, 'python paths');
    saveWorkbookPackages(packages, pythonPaths);
}

/**
 * Handle execution_result and execution_error messages
 */
export function handleExecutionResult(env, showErrorNotification) {
    window.logToServer('DEBUG', 'Execution result:', env);
    const source = env.source || 'addin';  // Default to 'addin' for backwards compatibility
    // Show error notification for execution errors
    if (source=='addin' && env.type === 'execution_error') {
        showErrorNotification(env.content || 'Execution error occurred');
    }
}

/**
 * Handle show_message_box from Python kernel (via Business Layer)
 * Shows a message box dialog with the specified message, title, and type
 * @param {object} env - The message envelope containing message, title, and msg_type
 */
export function handleShowMessageBox(env) {
    const message = env.message || '';
    const title = env.title || 'XPyCode';
    const msgType = env.msg_type || 'Info';  // Info, Warning, Error
    
    window.logToServer('DEBUG', 'Showing message box:', title, msgType, message);
    
    try {
        showMessageBoxDialog(message, title, msgType);
    } catch (err) {
        window.logToServer('ERROR', 'Error showing message box:', err);
    }
}

/**
 * Handle restart_addin message from Business Layer
 * Triggers the add-in to restart itself
 */
export async function handleRestartAddin(env) {
    window.logToServer('DEBUG', 'Received restart_addin message, restarting add-in...');
    
    // Import and call the restartAddinAction from actions-config
    const { restartAddinAction } = await import('../advanced-actions/actions-config.js');
    await restartAddinAction();
}

/**
 * Handle set_enable_events message from kernel
 */
export function handleSetEnableEvents(env) {
    // Default to true (enable) if not specified, matching DEFAULT_SETTINGS
    const enable = env.enable !== undefined ? env.enable : true;
    window.logToServer('DEBUG', `[MessageHandler] set_enable_events: ${enable}`);
    setSetting('enableEditorEvents', enable);
    saveSettings();
}

/**
 * Create a message handler map for routing messages to handlers
 */
export function createMessageHandlers(deps) {
    const {
        chunkHandler,
        contextManager,
        sendRaw,
        currentSettings,
        showErrorNotification,
        eventDispatcher,
        registerEventHandlerFn,
        unregisterEventHandlerFn,
        scanWorkbookObjectsFn,
        registerDynamicFunctionsFn,
        storeFunctions,
        handleFunctionResultFn,
        processMessageFn,
        pendingFunctionRequests,
        streamingInvocations,
        onMessageCallback
    } = deps;
    
    let consoleAppendCount = 0;
    
    return {
        'chunk': (env) => {
            handleChunk(env, chunkHandler, onMessageCallback);
        },
        'excel_request': async (env) => {
            await handleExcelRequest(env, contextManager, sendRaw);
        },
        'sys_request': async (env) => {
            await handleSysRequest(env, contextManager, sendRaw);
        },
        'stdout': (env) => {
            consoleAppendCount = handleStdout(env, consoleAppendCount, currentSettings);
        },
        'stderr': (env) => {
            consoleAppendCount = handleStderr(env, consoleAppendCount, currentSettings, showErrorNotification);
        },
        'get_modules_request': async (env) => {
            await handleGetModulesRequest(env, sendRaw);
        },
        'get_functions_request': async (env) => {
            await handleGetFunctionsRequest(env, sendRaw);
        },
        'get_packages_request': async (env) => {
            await handleGetPackagesRequest(env, sendRaw);
        },
        'get_events_request': async (env) => {
            await handleGetEventsRequest(env, sendRaw);
        },
        'save_module_request': async (env) => {
            await handleSaveModuleRequest(env, sendRaw);
        },
        'load_module_request': async (env) => {
            await handleLoadModuleRequest(env, sendRaw);
        },
        'delete_module_request': async (env) => {
            await handleDeleteModuleRequest(env, sendRaw);
        },
        'get_event_config_request': async (env) => {
            await handleGetEventConfigRequest(env, sendRaw, eventDispatcher);
        },
        'save_event_config_request': async (env) => {
            await handleSaveEventConfigRequest(env, sendRaw, eventDispatcher);
        },
        'register_handler_request': async (env) => {
            await handleRegisterHandlerRequest(env, sendRaw, registerEventHandlerFn);
        },
        'unregister_handler_request': async (env) => {
            await handleUnregisterHandlerRequest(env, sendRaw, unregisterEventHandlerFn);
        },
        'scan_objects_request': async (env) => {
            await handleScanObjectsRequest(env, sendRaw, scanWorkbookObjectsFn);
        },
        'sync_custom_functions': (env) => {
            handleSyncCustomFunctions(env, registerDynamicFunctionsFn, storeFunctions);
        },
        'batch_results': (env) => {
            handleBatchResults(env, handleFunctionResultFn);
        },
        'batch': async (env) => {
            await handleBatch(env, processMessageFn);
        },
        'function_execution_result': (env) => {
            handleFunctionExecutionResult(env, pendingFunctionRequests, contextManager);
        },
        'streaming_function_result': (env) => {
            handleStreamingFunctionResult(env, streamingInvocations, contextManager);
        },
        'save_workbook_packages': (env) => {
            handleSaveWorkbookPackages(env);
        },
        'execution_result': (env) => {
            handleExecutionResult(env, showErrorNotification);
        },
        'execution_error': (env) => {
            handleExecutionResult(env, showErrorNotification);
        },
        'show_message_box': (env) => {
            handleShowMessageBox(env);
        },
        'restart_addin': async (env) => {
            await handleRestartAddin(env);
        },
        'set_enable_events': (env) => {
            handleSetEnableEvents(env);
        }
    };
}
