// XPyCode Streaming Handler
// Handles execution of streaming Python UDFs (generator functions)

import { genId } from '../core/utils.js';
import { transformResultForDimension } from './udf-dispatcher.js';

/**
 * Streaming dispatcher for generator functions.
 * Unlike pythonDispatcher which returns a Promise, this uses the invocation object.
 * 
 * @param {string} functionId - The Excel function ID (sanitized)
 * @param {string} dimension - The dimension setting (Scalar, 1-Row, 1-Column, 2-D)
 * @param {Map} functionModuleMap - Map of function IDs to module/function info
 * @param {Map} streamingInvocations - Map of streaming invocations
 * @param {Object} contextManager - ContextManager instance for wire conversion
 * @param {Function} sendRaw - Function to send messages to server
 * @param {Array} args - The arguments passed to the function (includes invocation as last arg)
 */
export function streamingDispatcher(functionId, dimension, functionModuleMap, streamingInvocations, contextManager, sendRaw, ...args) {
    const requestId = genId();
    //Invocation is the last argument
    const invocation = args.pop();

    if (!(invocation && typeof invocation === 'object' && 'address' in invocation)){
        window.logToServer('ERROR', 'invocation not sent to the function.');
    }
    
    window.logToServer('DEBUG', 'streamingDispatcher called with functionId:', functionId, 'dimension:', dimension);
    
    // Look up function info
    if (!functionModuleMap || !functionModuleMap.has(functionId)) {
        window.logToServer('ERROR', 'Function not found in functionModuleMap. functionId:', functionId);
        window.logToServer('ERROR', 'Available function IDs:', functionModuleMap ? Array.from(functionModuleMap.keys()) : 'Map not initialized');
        invocation.setResult(`#ERROR: Function ${functionId} not registered`);
        return;
    }
    
    const funcInfo = functionModuleMap.get(functionId);
    const moduleName = funcInfo.module;
    const functionName = funcInfo.function;
    
    window.logToServer('DEBUG', 'Found function info - module:', moduleName, 'function:', functionName);
    
    // Convert args to wire format
    const towireArgs = args.map(a => contextManager.toWire(a, null));

    // Show initial processing state
    invocation.setResult("Processing...");

    // Store streaming invocation for result updates
    streamingInvocations.set(requestId, { invocation, dimension });
    
    // Set up cancellation handler
    invocation.onCanceled = () => {
        window.logToServer('DEBUG', 'Streaming function canceled:', requestId);
        streamingInvocations.delete(requestId);
        
        // Send cancellation to server
        sendRaw({
            type: 'cancel_streaming_function',
            request_id: requestId
        });
    };
    

    function startStreaming() {
        // Send streaming function execution request
        if (window.isInitialized) {
            const message = {
                type: 'streaming_function_execution',
                request_id: requestId,
                module_name: moduleName,
                function_name: functionName,
                args: towireArgs,
                streaming: true
            };

            window.logToServer('DEBUG', 'Sending streaming_function_execution:', moduleName + '.' + functionName, 'requestId:', requestId);
            sendRaw(message);
        }
        else {
            window.logToServer('WARNING', 'Cannot start streaming function: system not initialized');
            setTimeout(startStreaming, 500);
        }
    }
    startStreaming();

}

/**
 * Handle streaming function results from the server.
 * @param {Object} message - The streaming_function_result message
 * @param {Map} streamingInvocations - Map of streaming invocations
 * @param {Object} contextManager - ContextManager instance for wire conversion
 */
export function handleStreamingResult(message, streamingInvocations, contextManager) {
    const requestId = message.request_id;
    const result = message.result;
    const done = message.done;
    const error = message.error;
    
    const invocationInfo = streamingInvocations?.get(requestId);
    if (!invocationInfo) {
        // Invocation was canceled, ignore
        window.logToServer('DEBUG', 'Ignoring streaming result for canceled invocation:', requestId);
        return;
    }
    
    const { invocation, dimension } = invocationInfo;
    
    if (error) {
        invocation.setResult(`#ERROR: ${error}`);
        streamingInvocations.delete(requestId);
        return;
    }
    
    // Transform result based on dimension
    if (result){
        const transformedResult = transformResultForDimension(contextManager.fromWire(result), dimension);
        invocation.setResult(transformedResult);
    }
    
    if (done) {
        streamingInvocations.delete(requestId);
    }
}

/**
 * Cancel all active streaming invocations.
 * Called before re-registering functions.
 * @param {Map} streamingInvocations - Map of streaming invocations
 * @param {Function} sendRaw - Function to send messages to server
 */
export function cancelAllStreamingInvocations(streamingInvocations, sendRaw) {
    if (streamingInvocations && streamingInvocations.size > 0) {
        window.logToServer('DEBUG', 'Canceling', streamingInvocations.size, 'streaming invocations');
        
        for (const [requestId, info] of streamingInvocations) {
            // Send cancel to server
            sendRaw({
                type: 'cancel_streaming_function',
                request_id: requestId
            });
        }
        
        streamingInvocations.clear();
    }
}
