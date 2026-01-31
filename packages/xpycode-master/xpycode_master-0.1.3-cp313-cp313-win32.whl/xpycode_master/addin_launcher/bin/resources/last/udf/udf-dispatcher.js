// XPyCode UDF Dispatcher
// Handles execution of standard Python UDFs (non-streaming)

import { UDF_EXECUTION_TIMEOUT_MS } from '../core/constants.js';
import { genId } from '../core/utils.js';

/**
 * Generic Python function dispatcher for UDFs.
 * This function is called by Excel when a custom function is invoked.
 * It generates a unique request_id, sends a function_execution message to the server,
 * and returns a Promise that resolves with the result.
 * 
 * @param {string} functionId - The Excel function ID (sanitized)
 * @param {string} dimension - The dimension setting (Scalar, 1-Row, 1-Column, 2-D)
 * @param {Map} functionModuleMap - Map of function IDs to module/function info
 * @param {Map} pendingFunctionRequests - Map of pending requests
 * @param {Object} contextManager - ContextManager instance for wire conversion
 * @param {Function} sendRaw - Function to send messages to server
 * @param {Array} args - The arguments passed to the function
 * @returns {Promise} A promise that resolves with the function result
 */
export async function pythonDispatcher(functionId, dimension, functionModuleMap, pendingFunctionRequests, contextManager, sendRaw, ...args) {
    const requestId = genId();
    
    // Look up the module and function name from the function ID
    if (!functionModuleMap || !functionModuleMap.has(functionId)) {
        const errorMsg = `Function ${functionId} not registered`;
        window.logToServer('ERROR', `${errorMsg}`);
        return Promise.reject(new Error(errorMsg));
    }
    
    const funcInfo = functionModuleMap.get(functionId);
    const moduleName = funcInfo.module;
    const functionName = funcInfo.function;
    
    // Strip Excel invocation object if it's the last argument
    // Excel passes an invocation object (with 'address' property) as the last arg
    if (args.length > 0) {
        const lastArg = args[args.length - 1];
        if (lastArg && typeof lastArg === 'object' && 'address' in lastArg) {
            window.logToServer('DEBUG', 'Stripping Excel invocation object from args');
            args = args.slice(0, -1);
        }
    }
    const towire_args = []
    
    for (const a of args) {
        const val = contextManager.toWire(a, null); //No context needed as Custom Functions never give context linked object as args.
        towire_args.push(val);
    }
    
    
    return new Promise((resolve, reject) => {
        // Store the promise resolve/reject handlers
        pendingFunctionRequests.set(requestId, { resolve, reject });
        
        // Set a timeout to prevent hanging forever
        const timeout = setTimeout(() => {
            pendingFunctionRequests.delete(requestId);
            reject(new Error('Function execution timeout'));
        }, UDF_EXECUTION_TIMEOUT_MS);
        
        // Update the stored handlers to clear the timeout on completion
        const originalResolve = resolve;
        const originalReject = reject;
        pendingFunctionRequests.set(requestId, {
            resolve: (result) => {
                clearTimeout(timeout);
                const transformedResult = transformResultForDimension(result, dimension);
                originalResolve(transformedResult);
            },
            reject: (error) => {
                clearTimeout(timeout);
                originalReject(error);
            }
        });
        
        // Send function_execution message to server with separate module and function names
        const message = {
            type: 'function_execution',
            request_id: requestId,
            module_name: moduleName,
            function_name: functionName,
            args: towire_args
        };
        
        window.logToServer('DEBUG', 'Sending function_execution:', moduleName + '.' + functionName, 'requestId:', requestId);
        sendRaw(message);
    });
}

/**
 * Transform result based on dimension setting.
 * @param {*} result - The result to transform
 * @param {string} dimension - The dimension setting (Scalar, 1-Row, 1-Column, 2-D)
 * @returns {*} Transformed result
 */
export function transformResultForDimension(result, dimension) {
    if (dimension === "1-Row") {
        // Wrap in array for horizontal output
        return [result];
    } else if (dimension === "1-Column") {
        // Convert array to array of single-element arrays for vertical output
        if (Array.isArray(result)) {
            return result.map(r => [r]);
        } else {
            return [[result]];
        }
    } else {
        // Scalar or 2-D: no transformation
        return result;
    }
}

/**
 * Handle a function result message from the server.
 * @param {Object} message - The function_execution_result message
 * @param {Map} pendingFunctionRequests - Map of pending requests
 * @param {Object} contextManager - ContextManager instance for wire conversion
 */
export function handleFunctionResult(message, pendingFunctionRequests, contextManager) {
    const requestId = message.request_id;
    const pending = pendingFunctionRequests.get(requestId);
    
    // Always output logs to console if present
    if (message.logs) {
        window.logToServer('DEBUG', 'Function logs:', message.logs);
    }
    
    if (pending) {
        pendingFunctionRequests.delete(requestId);
        
        if (message.status === 'success') {
            window.logToServer('DEBUG', 'Function execution succeeded:', requestId, message.result);
            // Deserialize the result using fromWire to preserve type information
            let deserializedResult = message.result;
            if (message.result) {
                try {
                    deserializedResult = contextManager.fromWire(message.result, null);
                    window.logToServer('DEBUG', 'Deserialized result:', requestId, deserializedResult);
                } catch (err) {
                    window.logToServer('WARNING', 'Failed to deserialize result, using raw value:', err);
                    deserializedResult = message.result;
                }
            }
            pending.resolve(deserializedResult);
        } else if (message.status === 'error') {
            // Print traceback to console
            window.logToServer('ERROR', 'Function execution failed:', requestId);
            if (message.error) {
                window.logToServer('ERROR', 'Traceback:', message.error);
            }
            
            // Throw Excel custom function error
            const error = new CustomFunctions.Error(CustomFunctions.ErrorCode.invalidValue);
            pending.reject(error);
        } else {
            // Unknown status - treat as error
            window.logToServer('ERROR', 'Function execution unknown status:', requestId, message);
            const error = new CustomFunctions.Error(CustomFunctions.ErrorCode.invalidValue);
            pending.reject(error);
        }
    } else {
        window.logToServer('WARNING', 'Received function_execution_result for unknown request_id:', requestId);
    }
}
