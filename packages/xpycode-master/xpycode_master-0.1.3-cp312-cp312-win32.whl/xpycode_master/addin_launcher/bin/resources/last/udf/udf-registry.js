// XPyCode UDF Registry
// Handles registration of custom functions with Excel

import { INVALID_FUNCTION_ID } from '../core/constants.js';
import { isOfficeSettingsAvailable, safeJsonStringify, safeJsonParse } from '../storage/package-storage.js';
import { cancelAllStreamingInvocations } from './streaming-handler.js';
import { pythonDispatcher } from './udf-dispatcher.js';
import { streamingDispatcher } from './streaming-handler.js';

/**
 * Sanitize a function ID to ensure Excel compatibility.
 * Excel function IDs can contain alphanumeric characters and underscores.
 * This sanitization removes special characters while preserving underscores.
 * 
 * @param {string} name - The function name to sanitize
 * @returns {string} Sanitized function ID (alphanumeric and underscores only)
 */
export function sanitizeFunctionId(name) {
    if (!name || typeof name !== 'string') {
        return INVALID_FUNCTION_ID;
    }
    // Remove all non-alphanumeric characters except underscores
    // Keep letters, numbers, and underscores (e.g., X.P.C_COUCOU -> XPC_COUCOU)
    return name.toUpperCase().replace(/[^A-Z0-9_]/g, '');
}

/**
 * Validate and normalize parameter metadata.
 * Ensures parameters is always an array with valid type information.
 * 
 * @param {Array|undefined} parameters - Parameter array from Business Layer
 * @returns {Array} Validated parameter array
 */
export function validateParameters(parameters) {
    if (!Array.isArray(parameters)) {
        window.logToServer('WARNING', 'Parameters is not an array, defaulting to empty array');
        return [];
    }
    
    return parameters.map((param, index) => {
        // Handle both old format (strings) and new format (objects with name and type)
        let paramName;
        
        if (typeof param === 'string') {
            // Legacy format: just parameter name
            paramName = param;
        } else if (param && typeof param === 'object') {
            // New format: object with name and type
            paramName = param.name || `arg${index}`;
        } else {
            // Invalid format
            window.logToServer('WARNING', 'Invalid parameter format at index', index, ':', param);
            paramName = `arg${index}`;
        }
        
        // Per requirements: Always use 'any' type regardless of Python type hints
        // This ensures maximum compatibility with Excel's dynamic typing system
        return {
            name: paramName,
            description: `Parameter ${paramName}`,
            type: 'any'
        };
    });
}

/**
 * Validate metadata structure for Excel Custom Function registration.
 * Ensures the metadata object has all required fields in the correct format.
 * This prevents Excel crashes from malformed metadata.
 * 
 * @param {Object} metadata - Metadata object to validate
 * @returns {boolean} True if metadata is valid, false otherwise
 */
export function validateMetadata(metadata) {
    // Check top-level structure
    if (!metadata || typeof metadata !== 'object') {
        window.logToServer('ERROR', 'Metadata is not an object');
        return false;
    }
    
    if (!Array.isArray(metadata.functions)) {
        window.logToServer('ERROR', 'Metadata.functions is not an array');
        return false;
    }
    
    // Validate each function in the metadata
    for (let i = 0; i < metadata.functions.length; i++) {
        const func = metadata.functions[i];
        
        // Check required fields
        if (!func.id || typeof func.id !== 'string') {
            window.logToServer('ERROR', 'Function at index', i, 'missing valid id');
            return false;
        }
        
        if (!func.name || typeof func.name !== 'string') {
            window.logToServer('ERROR', 'Function at index', i, 'missing valid name');
            return false;
        }
        
        // Validate parameters array
        if (!Array.isArray(func.parameters)) {
            window.logToServer('ERROR', 'Function', func.id, 'parameters is not an array');
            return false;
        }
        
        // Validate each parameter
        for (let j = 0; j < func.parameters.length; j++) {
            const param = func.parameters[j];
            if (!param.name || typeof param.name !== 'string') {
                window.logToServer('ERROR', 'Function', func.id, 'parameter at index', j, 'missing valid name');
                return false;
            }
            if (!param.type || typeof param.type !== 'string') {
                window.logToServer('ERROR', 'Function', func.id, 'parameter', param.name, 'missing valid type');
                return false;
            }
        }
        
        // Validate result object
        if (!func.result || typeof func.result !== 'object') {
            window.logToServer('ERROR', 'Function', func.id, 'missing valid result object');
            return false;
        }
        
        if (!func.result.type || typeof func.result.type !== 'string') {
            window.logToServer('ERROR', 'Function', func.id, 'result missing valid type');
            return false;
        }
    }
    
    return true;
}

/**
 * Associate functions with their dispatchers.
 * Creates the dispatcher functions and associates them with Excel.
 * 
 * @param {Array} functionList - List of function definitions
 * @param {Map} functionModuleMap - Map to store function ID -> module/function mappings
 * @param {Map} pendingFunctionRequests - Map of pending function requests
 * @param {Map} streamingInvocations - Map of streaming invocations
 * @param {Object} contextManager - ContextManager instance
 * @param {Function} sendRaw - Function to send messages to server
 * @returns {Array} List of successfully associated functions
 */
export function associateFunctions(functionList, functionModuleMap, pendingFunctionRequests, streamingInvocations, contextManager, sendRaw) {
    const associatedFunctions = [];
    
    for (const func of functionList) {
        const moduleName = func.module;
        const functionName = func.function;
        const excelName = func.excel_name;
        const parameters = func.parameters || [];
        const dimension = func.dimension || "Scalar";
        const streaming = func.streaming || false;
        
        if (!moduleName || !functionName || !excelName) {
            window.logToServer('WARNING', 'Skipping invalid function entry (missing module/function/excel_name):', func);
            continue;
        }
        
        // Sanitize function ID to ensure Excel compatibility
        // Excel requires alphanumeric characters only (no underscores)
        const functionId = sanitizeFunctionId(excelName);
        
        if (functionId === INVALID_FUNCTION_ID || functionId.length === 0) {
            window.logToServer('ERROR', 'Cannot sanitize function name:', excelName);
            continue;
        }
        
        // Store the module and function mapping for this Excel function ID
        functionModuleMap.set(functionId, { module: moduleName, function: functionName, dimension: dimension, streaming: streaming });
        
        // Create the appropriate dispatcher function based on streaming flag
        let funcImpl;
        if (streaming) {
            // Create streaming function that receives invocation object
            funcImpl = (...args) => {
                streamingDispatcher(functionId, dimension, functionModuleMap, streamingInvocations, contextManager, sendRaw, ...args);
            };
        } else {
            // Create regular async function
            funcImpl = async (...args) => {
                return pythonDispatcher(functionId, dimension, functionModuleMap, pendingFunctionRequests, contextManager, sendRaw, ...args);
            };
        }
        
        // Associate the function ID with the dispatcher
        // This must complete successfully before proceeding to metadata registration
        try {
            CustomFunctions.associate(functionId, funcImpl);
            window.logToServer('DEBUG', 'Associated function:', functionId, '->', moduleName + '.' + functionName, streaming ? '(streaming)' : '(regular)');
            
            // Store successfully associated function for metadata generation
            associatedFunctions.push({
                functionId: functionId,
                moduleName: moduleName,
                functionName: functionName,
                parameters: parameters,
                dimension: dimension,
                streaming: streaming
            });
        } catch (associateErr) {
            window.logToServer('ERROR', 'Error associating function:', functionId, associateErr);
            // Skip this function - do not add to metadata
            continue;
        }
    }
    
    return associatedFunctions;
}

/**
 * Build function metadata for Excel Custom Function Manager.
 * 
 * @param {Array} associatedFunctions - List of successfully associated functions
 * @returns {Object} Metadata object
 */
export function buildFunctionMetadata(associatedFunctions) {
    const metadata = {
        functions: []
    };
    
    for (const funcInfo of associatedFunctions) {
        // Validate and normalize parameters
        const validatedParams = validateParameters(funcInfo.parameters);
        
        // Determine result type based on dimension
        let resultType = "any";
        let dimensionality;
        let dimensions;
        if (funcInfo.dimension === "1-Row" || funcInfo.dimension === "1-Column") {
            dimensions = 1;
            dimensionality = "matrix";
        } else if (funcInfo.dimension === "2-D") {
            dimensions = 2;
            dimensionality = "matrix";
        }
        // else: Scalar (default) - dimensionality and dimensions remain undefined
        
        
        // Generate metadata for this function
        // The metadata describes the function for Excel's formula engine
        const functionMetadata = {
            id: funcInfo.functionId,
            name: funcInfo.functionId,
            description: `Python function: ${funcInfo.moduleName}.${funcInfo.functionName}`,
            parameters: validatedParams,
            result: {
                type: resultType
            },
            options: {
                stream: funcInfo.streaming,
                cancelable: funcInfo.streaming
            }
        };
        
        // Add dimensionality if applicable
        
        if (dimensionality) {
            functionMetadata.result.dimensionality = dimensionality;
        }
        

        if (dimensions) {
            functionMetadata.result.dimensions = dimensions;
        }


        metadata.functions.push(functionMetadata);
    }
    
    return metadata;
}

/**
 * Register metadata with Excel CustomFunctionManager.
 * 
 * @param {Object} metadata - Metadata object
 * @param {Function} logToServer - Function to log to server
 * @returns {Promise<void>}
 */
export async function registerWithExcel(metadata, logToServer) {
    try {
        // Validate metadata structure before registration
        // This check prevents Excel crashes from malformed JSON
        if (!validateMetadata(metadata)) {
            window.logToServer('ERROR', 'Metadata validation failed, aborting registration');
            window.logToServer('DEBUG', 'Functions are associated but metadata is invalid');
            return;
        }
        
        // Serialize metadata to JSON string
        let metadataStr;
        try {
            metadataStr = JSON.stringify(metadata);
            window.logToServer('DEBUG', 'Metadata to register:', metadataStr);
        } catch (jsonErr) {
            window.logToServer('ERROR', 'Failed to serialize metadata to JSON:', jsonErr);
            window.logToServer('DEBUG', 'Functions are associated but metadata cannot be serialized');
            return;
        }
        
        /* FOR COMPLEX DEBUG USAGE ONLY*/
        /*
        // Log the metadata to the server before registration
        // This ensures we capture the exact payload even if Excel crashes
        logToServer('Pre-registration metadata', {
            metadataString: metadataStr,
            metadata: metadata,
            functionCount: metadata.functions.length
        });
        */
        
        // Try to register with CustomFunctionManager
        // Note: The register API may not be available in all Excel versions
        // In such cases, the functions are still usable via associate()
        if (typeof Excel !== 'undefined' && Excel.CustomFunctionManager) {
            try {
                // Some versions use Excel.CustomFunctionManager.register directly
                if (typeof Excel.CustomFunctionManager.register === 'function') {
                    try {
                        await Excel.CustomFunctionManager.register(metadataStr,"");
                        window.logToServer('DEBUG', 'Successfully registered metadata for', metadata.functions.length, 'functions');
                    } catch (registerDirectErr) {
                        window.logToServer('ERROR', 'Error calling CustomFunctionManager.register:', registerDirectErr);
                        window.logToServer('ERROR', 'Error details:', {
                            message: registerDirectErr.message,
                            name: registerDirectErr.name,
                            stack: registerDirectErr.stack
                        });
                        // Error is handled by outer catch block
                    }
                } else {
                    // Some versions require creating a manager instance via Excel.run
                    await Excel.run(async (context) => {
                        if (Excel.CustomFunctionManager.newObject) {
                            const cfManager = Excel.CustomFunctionManager.newObject(context);
                            // Validate that the manager has a register method
                            if (cfManager && typeof cfManager.register === 'function') {
                                try {
                                    await cfManager.register(metadataStr);
                                    await context.sync();
                                    window.logToServer('DEBUG', 'Successfully registered metadata for', metadata.functions.length, 'functions');
                                } catch (registerContextErr) {
                                    window.logToServer('ERROR', 'Error in cfManager.register:', registerContextErr);
                                    window.logToServer('ERROR', 'Error details:', {
                                        message: registerContextErr.message,
                                        name: registerContextErr.name,
                                        stack: registerContextErr.stack
                                    });
                                    // Error is handled by outer catch block
                                }
                            } else {
                                window.logToServer('WARNING', 'CustomFunctionManager instance lacks register method, using associate only');
                            }
                        } else {
                            window.logToServer('WARNING', 'CustomFunctionManager.newObject not available, using associate only');
                        }
                    });
                }
            } catch (registerErr) {
                window.logToServer('WARNING', 'Error during metadata registration:', registerErr);
                window.logToServer('WARNING', 'This is non-fatal - functions are associated and may work without explicit metadata registration');
                window.logToServer('DEBUG', 'Functions are still available via CustomFunctions.associate');
            }
        } else {
            window.logToServer('WARNING', 'CustomFunctionManager not available, using associate only');
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error in registration phase:', err);
        window.logToServer('DEBUG', 'Functions are associated but metadata registration failed');
        window.logToServer('DEBUG', 'This is non-fatal - functions may still work');
    }
}

/**
 * Persist functions to workbook settings.
 * 
 * @param {Array} functionList - List of function definitions
 */
export function persistFunctions(functionList) {
    try {
        if (isOfficeSettingsAvailable()) {
            // Store the function list metadata
            const functionsJson = safeJsonStringify(functionList, 'function list for persistence');
            
            if (functionsJson) {
                Office.context.document.settings.set("XPyCode_Functions", functionsJson);
                // Save settings asynchronously
                Office.context.document.settings.saveAsync((asyncResult) => {
                    if (asyncResult.status === Office.AsyncResultStatus.Succeeded) {
                        window.logToServer('DEBUG', 'Function metadata persisted to workbook settings');
                    } else {
                        window.logToServer('ERROR', 'Failed to persist function metadata:', asyncResult.error.message);
                    }
                });
            } else {
                window.logToServer('WARNING', 'Functions will not be persisted to workbook settings');
            }
        } else {
            window.logToServer('WARNING', 'Office.context.document.settings not available, skipping persistence');
        }
    } catch (persistErr) {
        window.logToServer('ERROR', 'Error persisting function metadata:', persistErr);
    }
}

/**
 * Register dynamic custom functions with Excel.
 * Main orchestrator for the UDF registration flow.
 * 
 * @param {Array} functionList - List of function definitions with module, function, excel_name, and parameters
 * @param {Map} functionModuleMap - Map to store function ID -> module/function mappings
 * @param {Map} pendingFunctionRequests - Map of pending function requests
 * @param {Map} streamingInvocations - Map of streaming invocations
 * @param {Object} contextManager - ContextManager instance
 * @param {Function} sendRaw - Function to send messages to server
 * @param {Function} logToServer - Function to log to server
 * @returns {Promise<void>}
 */
export async function registerDynamicFunctions(functionList, functionModuleMap, pendingFunctionRequests, streamingInvocations, contextManager, sendRaw, logToServer) {
    if (!functionList || functionList.length === 0) {
        window.logToServer('DEBUG', 'No functions to register');
        return;
    }
    
    window.logToServer('DEBUG', 'Registering', functionList.length, 'custom functions');
    
    // Cancel existing streaming functions first
    cancelAllStreamingInvocations(streamingInvocations, sendRaw);
    
    try {
        // Check if CustomFunctions API is available
        if (typeof CustomFunctions === 'undefined' || typeof Excel === 'undefined') {
            window.logToServer('WARNING', 'CustomFunctions API not available in this context');
            window.logToServer('DEBUG', 'Functions stored for later registration');
            return;
        }
        
        // Step 1: Associate each function with the generic dispatcher
        const associatedFunctions = associateFunctions(
            functionList,
            functionModuleMap,
            pendingFunctionRequests,
            streamingInvocations,
            contextManager,
            sendRaw
        );
        
        // Step 2: Generate metadata for Excel.CustomFunctionManager.register
        const metadata = buildFunctionMetadata(associatedFunctions);
        
        // Step 3: Register the metadata with Excel's Custom Function Manager
        await registerWithExcel(metadata, logToServer);
        
        window.logToServer('DEBUG', 'Successfully processed', functionList.length, 'custom functions');
        
        // Step 4: Persist the functions metadata to workbook settings
        persistFunctions(functionList);
    } catch (err) {
        window.logToServer('ERROR', 'Error in registerDynamicFunctions:', err);
    }
}

/**
 * Sync persisted custom functions from workbook settings on startup.
 * 
 * @param {Function} registerFn - The registerDynamicFunctions function
 * @param {Function} sendRaw - Function to send messages to server
 */
export function syncFunctionsOnStartup(registerFn, sendRaw) {
    try {
        if (!isOfficeSettingsAvailable()) {
            window.logToServer('DEBUG', 'Office settings not available, skipping function sync');
            return;
        }
        
        const savedFunctionsJson = Office.context.document.settings.get("XPyCode_Functions");
        if (!savedFunctionsJson) {
            window.logToServer('DEBUG', 'No persisted functions found');
            return;
        }
        
        const savedFunctions = safeJsonParse(savedFunctionsJson, 'saved function metadata');
        
        if (savedFunctions && Array.isArray(savedFunctions) && savedFunctions.length > 0) {
            window.logToServer('DEBUG', 'Syncing', savedFunctions.length, 'persisted functions with server');

            registerFn(savedFunctions);
            sendRaw({
                type: 'client_sync_functions',
                functions: savedFunctions
            });
            
            window.logToServer('DEBUG', 'Sent client_sync_functions message to server');
        } else if (savedFunctions !== null) {
            window.logToServer('DEBUG', 'No valid persisted functions to sync');
        } else {
            window.logToServer('WARNING', 'Saved function data may be corrupted');
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error syncing functions on startup:', err);
    }
}

/**
 * Register persisted custom functions from workbook settings on startup.
 */
export function getRegisteredFunctions() {
    try {
        if (!isOfficeSettingsAvailable()) {
            window.logToServer('DEBUG', 'Office settings not available, skipping function sync');
            return [];
        }

        const savedFunctionsJson = Office.context.document.settings.get("XPyCode_Functions");
        if (!savedFunctionsJson) {
            window.logToServer('DEBUG', 'No persisted functions found');
            return [];
        }

        const savedFunctions = safeJsonParse(savedFunctionsJson, 'saved function metadata');

        if (savedFunctions && Array.isArray(savedFunctions)) {
            window.logToServer('DEBUG', 'Syncing', savedFunctions.length, 'persisted functions with server');

            window.logToServer('DEBUG', 'Sent client_sync_functions message to server');
            return savedFunctions;

        } else if (savedFunctions !== null) {
            window.logToServer('DEBUG', 'No valid persisted functions to sync');
        } else {
            window.logToServer('WARNING', 'Saved function data may be corrupted');
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error syncing functions on startup:', err);
    }
    return [];
}
