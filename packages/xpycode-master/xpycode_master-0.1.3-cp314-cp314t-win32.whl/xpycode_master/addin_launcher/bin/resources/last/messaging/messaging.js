// XPyCode Messaging
// Slim messaging class - handles WebSocket connection and message routing

import { ChunkHandler } from './chunk-handler.js';
import { createMessageHandlers } from './message-handlers.js';
import { genId } from '../core/utils.js';
import { getEventConfigFromWorkbook } from '../storage/event-config-storage.js';
import { syncPackagesOnStartup } from '../storage/package-storage.js';
import { registerDynamicFunctions, syncFunctionsOnStartup, getRegisteredFunctions } from '../udf/udf-registry.js';
import { WorkbookWatcher } from '../watcher/workbook-watcher.js';
import { handleFunctionResult } from '../udf/udf-dispatcher.js';
// Utils imports
import { reloadConfig, isLoggingLevelEnabled, getEventsDictionary, getWorkbookTree } from '../utils/index.js';


/**
 * Messaging class
 * Handles WebSocket communication with the Python backend
 */
export class Messaging {
    constructor(host, port, workbookId,workbookName, contextManager, frontendPythonConsole, opts = {}) {
        // Store the full URL with all query parameters (including workbook name)
        // This URL is reused for reconnections to preserve the workbook identity
        this.host=host;
		this.port=port;
		this.workbookId=workbookId;
		this.workbookName=workbookName;
		this.url = this.getUrl();
        this.ws = null;
        this.frontendPythonConsole = frontendPythonConsole;
        this.pending = new Map();
        this.ctx = contextManager;
        this._closed = false;
        this._wellOpened = false;
        this.eventDispatcher = null; // Set via setEventDispatcher() after creation
        const defaults = { backoffMs: [500, 1000, 2000, 5000, 8000], maxBackoffMs: 15000 };
        this.opts = { ...defaults, ...opts };
        
        // Custom functions state (for UDF registration)
        this._customFunctions = [];
        this._functionModuleMap = new Map();
        
        // Pending function execution requests: Map<request_id, {resolve, reject}>
        this._pendingFunctionRequests = new Map();
        
        // Streaming invocations: Map<request_id, {invocation, dimension}>
        this._streamingInvocations = new Map();
        
        // Chunk handler
        this._chunkHandler = new ChunkHandler();
        
        // Workbook name and path tracking
        //this._workbookName = this._extractNameFromUrl(url);
        this._workbookPath = null;  // Track workbook path (null if not saved)
        
        // Initialize workbook watcher
        this._watcher = new WorkbookWatcher(
            (msg) => this.sendRaw(msg),
            () => this._scanWorkbookObjects(),
            () => this._checkWorkbookNameChange()
        );
        
        // Log the stored URL for debugging reconnection issues
        window.logToServer('DEBUG', 'Messaging initialized with URL:', this.url);
    }

    /**
     * Extract workbook name from URL query parameter.
     * @param {string} url - WebSocket URL with query parameters
     * @returns {string} Extracted workbook name or 'Untitled'
     */
    _extractNameFromUrl(url) {
        try {
            const urlObj = new URL(url);
            return decodeURIComponent(urlObj.searchParams.get('name') || 'Untitled');
        } catch (e) {
            return 'Untitled';
        }
    }
	
	getUrl(){
		const encodedName = encodeURIComponent(this.workbookName);
		return `ws://${this.host}:${this.port}/ws/addin/${this.workbookId}?name=${encodedName}`;
	}

    /**
     * Set the event dispatcher for handling event subscriptions
     * @param {EventDispatcher} dispatcher - The event dispatcher instance
     */
    setEventDispatcher(dispatcher) {
        this.eventDispatcher = dispatcher;
    }

    /**
     * Load event configuration from workbook and apply to EventDispatcher.
     * This is the public API for initializing event listeners.
     */
    async loadAndApplyEventConfig() {
        if (!this.eventDispatcher) {
            window.logToServer('WARNING', 'Cannot apply event config: EventDispatcher not set');
            return;
        }

        try {
            const config = await getEventConfigFromWorkbook();
            if (config) {
                window.logToServer('DEBUG', 'Loading event config:', config);
                await this.eventDispatcher.applyConfig(config);
            }
        } catch (err) {
            window.logToServer('WARNING', 'Error loading event config:', err);
        }
    }

    /**
     * Check if workbook name or path has changed and notify server.
     * Called periodically by the background watcher.
     */
    async _checkWorkbookNameChange() {
        try {
            await Excel.run(async (context) => {
                const workbook = context.workbook;
                workbook.load('name');
                
                // Load properties to get the path
                const properties = workbook.properties;
                properties.load('path');
                
                await context.sync();
                
                const currentName = workbook.name || 'Untitled';
                const currentPath = properties.path || null;
                
                // Check if name OR path changed
                const nameChanged = currentName !== this.workbookName;
                const pathChanged = currentPath !== this._workbookPath;
                
                if (nameChanged || pathChanged) {
                    const oldName = this.workbookName;
                    const oldPath = this._workbookPath;
                    
                    window.logToServer('DEBUG', 'Workbook changed:', {
                        nameChanged,
                        pathChanged,
                        oldName,
                        newName: currentName,
                        oldPath,
                        newPath: currentPath
                    });
                    
                    this.workbookName = currentName;
                    this._workbookPath = currentPath;
                    
                    // Update the URL for future reconnections
                    if (nameChanged) {
						this.url=this.getUrl();
                        //this._updateUrlWithNewName(currentName);
                    }
                    
                    // Notify server of name/path change
                    this.sendRaw({
                        type: 'workbook_name_changed',
                        old_name: oldName,
                        new_name: currentName,
                        path: currentPath
                    });
                }
            });
        } catch (err) {
            window.logToServer('ERROR', 'Error checking workbook name/path:', err);
        }
    }
	
	async _updatePort()
	{
		await reloadConfig();
		this.port=(window.XPYCODE_CONFIG && window.XPYCODE_CONFIG.serverPort) || DEFAULT_SERVER_PORT;
	}

    /**
     * Update the stored URL with the new workbook name.
     * This ensures reconnections use the updated name.
     * @param {string} newName - New workbook name
     */
    _updateUrlWithNewName(newName) {
        try {
            const urlObj = new URL(this.url);
            urlObj.searchParams.set('name', encodeURIComponent(newName));
            this.url = urlObj.toString();
            window.logToServer('DEBUG', 'Updated URL for reconnection:', this.url);
        } catch (err) {
            window.logToServer('ERROR', 'Error updating URL:', err);
        }
    }

    /**
     * Send event definitions to the server.
     * Gets metadata from office_tools.getEventsDictionary().
     */
    _sendEventDefinitions() {
        try {
            const eventDefinitions = getEventsDictionary();
            window.logToServer('DEBUG', 'Sending event definitions:', eventDefinitions);
            
            this.sendRaw({
                type: 'event_definitions_update',
                definitions: eventDefinitions
            });
        } catch (err) {
            window.logToServer('ERROR', 'Error sending event definitions:', err);
        }
    }

	// Helpers (put these in your class)
	_sleep(ms) {
	  return new Promise(r => setTimeout(r, ms));
	}

	_backoffDelay(attempt) {
	  const base = this.opts.baseBackoffMs ?? 250;
	  const max = this.opts.maxBackoffMs ?? 10_000;
	  const factor = this.opts.backoffFactor ?? 2;

	  const exp = Math.min(max, base * Math.pow(factor, attempt));
	  const jitterRatio = this.opts.jitterRatio ?? 0.2; // 20% jitter
	  const jitter = exp * jitterRatio * (Math.random() * 2 - 1); // [-jitter, +jitter]
	  return Math.max(0, Math.floor(exp + jitter));
	}

	_clearReconnectTimer() {
	  if (this._reconnectTimer) {
		clearTimeout(this._reconnectTimer);
		this._reconnectTimer = null;
	  }
	}

	_safeCloseWs(ws, code = 1000, reason = 'client closing') {
	  try {
		ws.onopen = ws.onclose = ws.onerror = ws.onmessage = null;
		if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
		  ws.close(code, reason);
		}
	  } catch (_) {}
	}

    async _startHeartbeat() {
        this._stopHeartbeat();
        this._heartbeatInterval = setInterval(() => {
            if (this._wellOpened && this.ws?.readyState === WebSocket.OPEN) {
                try {
                    this.sendRaw({ type: 'ping' });
                } catch (e) {
                    // Connection may be dead
                    window.logToServer('WARNING', 'Heartbeat failed:', e);
                }
            }
        }, 30000); // Every 30 seconds
    }

    _stopHeartbeat() {
        try {
            if (this._heartbeatInterval) {
                clearInterval(this._heartbeatInterval);
                this._heartbeatInterval = null;
            }
        } catch (_) { }
    }

	// Main connect logic
	async connect() {
	  if (this._closed) return;
	  if (this._wellOpened) return;
	  if (this._connecting) return this._connecting; // de-dupe concurrent calls

	  this._clearReconnectTimer();
      this._stopHeartbeat();

	  const connectTimeoutMs = this.opts.connectTimeoutMs ?? 8000;
	  const maxRetries = this.opts.maxRetries ?? Infinity;

	  // token used to invalidate older connection attempts
	  const myAttemptToken = (this._connectAttemptToken = (this._connectAttemptToken ?? 0) + 1);

	  let attempt = 0;

	  this._connecting = (async () => {
		while (!this._closed && !this._wellOpened && attempt < maxRetries) {
		  await this._updatePort();

		  window.logToServer('DEBUG', 'Attempting to connect to server at:', this.url);

		  let ws = null;
		  let timeoutId = null;

		  try {
			await new Promise((resolve, reject) => {
			  ws = new WebSocket(this.url);

			  // If this attempt becomes stale (another connect() started), abort it.
			  const staleGuard = () => this._connectAttemptToken !== myAttemptToken || this._closed;

			  timeoutId = setTimeout(() => {
				if (staleGuard()) return;
				reject(new Error('connect timeout'));
				this._safeCloseWs(ws, 1000, 'connect timeout');
			  }, connectTimeoutMs);

			  ws.onopen = () => {
				if (staleGuard()) {
				  this._safeCloseWs(ws, 1000, 'stale connect');
				  return;
				}

				clearTimeout(timeoutId);

				// Ensure only one live ws
				if (this.ws && this.ws !== ws) this._safeCloseWs(this.ws, 1000, 'replaced');

				this.ws = ws;
				this._wellOpened = true;
                this._startHeartbeat();
				window.logToServer('DEBUG', 'WebSocket connection established');


				try {
				  this._watcher.start();
				} catch (e) {
				  window.logToServer('ERROR', 'Failed to start watcher:', e);
				}
                this.frontendPythonConsole.setConnected(true);
                this.frontendPythonConsole.log('Connection opened');

				resolve();
			  };

			  ws.onerror = (e) => {
				// Many browsers don’t give details; treat as connection failure if not open.
				if (staleGuard()) return;

				// If it already opened, let onclose drive reconnection.
				if (this._wellOpened && ws === this.ws) {
                    this._stopHeartbeat();
                    window.logToServer('ERROR', 'WebSocket error:', e);
                    return;
				}

				clearTimeout(timeoutId);
				reject(e instanceof Error ? e : new Error('ws error'));
				this._safeCloseWs(ws, 1000, 'error before open');
			  };

			  ws.onmessage = (ev) => {
				// Ignore messages from stale sockets
				if (ws !== this.ws) return;
				// Use direct console.error to avoid infinite recursion during logging
				this._onMessage(ev).catch(err => console.error('[XPyCode] Error in _onMessage:', err));
			  };

			  ws.onclose = async () => {
				if (staleGuard()) return;

				const wasCurrent = ws === this.ws;

				window.logToServer('DEBUG', 'WebSocket connection closed');

				// Only mutate connection state if the socket being closed is the current one
				if (wasCurrent) {
				  this._wellOpened = false;
				  this.ws = null;

				  try {
					this._watcher.stop();
				  } catch (e) {
					window.logToServer('ERROR', 'Error stopping watcher:', e);
                  }
                  this._stopHeartbeat();

				  if (!this._closed) {
					try {
					  await this.onServerClosing();
					} catch (e) {
					  window.logToServer('ERROR', 'Error in onServerClosing:', e);
					}

					// schedule reconnect (do not block on it inside onclose)
					const delay = this._backoffDelay(attempt);
					this._clearReconnectTimer();
					this._reconnectTimer = setTimeout(() => {
					  // Fire-and-forget; connect() de-dupes via this._connecting
					  // Use direct console.error to avoid infinite recursion during logging
					  this.connect().catch(err => console.error('[XPyCode] Error reconnecting:', err));
					}, delay);
				  }
				}
			  };
			});

			// success
			return;
		  } catch (err) {
			clearTimeout(timeoutId);

			// If we got closed in the meantime, bail out
			if (this._closed || this._connectAttemptToken !== myAttemptToken) return;

			this._wellOpened = false;
			if (ws && ws === this.ws) this.ws = null;

			const delay = this._backoffDelay(attempt);
			attempt += 1;

			// Don’t spam logs; but keep one line visible
			window.logToServer('WARNING', 'Connect failed; retrying in', delay, 'ms', err?.message ?? err);

			await this._sleep(delay);
		  }
		}
	  })().finally(() => {
		// allow future connect() calls after loop finishes
		this._connecting = null;
	  });

	  return this._connecting;
	}

    /**
     * Close the WebSocket connection
     */
    close() { 
        this._closed = true;
        this._watcher.stop();
        try { this.ws?.close(); } catch (_) { }
    }
	
    /**
     * Check if connection is open
     */
    isOpen() { 
        return this._wellOpened;
    }
	

    /**
     * Handle server disconnection and initiate reconnection
     */
    async onServerClosing() {
        window.logToServer('DEBUG', 'Server connection closed, reconnecting with URL:', this.url);
        this.ctx.liveInstances.clear();
        this.ctx.ensureContext();
		this._wellOpened = false;
        this.frontendPythonConsole.setConnected(false);
        this.frontendPythonConsole.setStatus('Connection closed', 'error');
        this.frontendPythonConsole.log('Connection closed');

        // Reconnect using the stored URL which includes the workbook name
        this.connect();
    }

    /**
     * Send a raw message over WebSocket
     * @param {Object} payload - Message payload
     */
    sendRaw(payload) {
        this.ws.send(JSON.stringify(payload));
    }

    /**
     * Send a request and wait for response
     * @param {Object} req - Request object
     * @returns {Promise} Promise that resolves with the response
     */
    sendRequest(req) {
        return new Promise((resolve, reject) => {
            const requestId = genId();
            const envelope = { ...req, requestId, kind: 'request' };
            this.pending.set(requestId, { resolve, reject });
            this.sendRaw(envelope);
        });
    }

    /**
     * Send an error response
     * @param {string} requestId - Request ID
     * @param {string} message - Error message
     */
    sendError(requestId, message) {
        this.sendRaw({ kind: 'response', requestId, ok: false, error: { message } });
    }

    /**
     * Get the caller file path and line from the stack trace.
     * @param {number} skip - Number of stack frames to skip (default 3: Error + callerLine + logToServer)
     * @returns {string} Caller information string
     */
    _getCallerInfo(skip = 3) {
        const stack = new Error().stack;
        if (!stack) return "";
        const lines = stack.split("\n").map(s => s.trim());
        // Return empty string if skip is negative or out of bounds
        return (skip >= 0 && skip < lines.length) ? lines[skip] : "";
    }

    /**
     * Log messages to the Python server with level and caller tracking.
     * Also logs to browser console before sending to server.
     * 
     * @param {string} level - Log level: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
     * @param {...any} messages - Messages to log (will be stringified)
     */
    logToServer(level, ...messages) {
        // Validate level
        const validLevels = ['DEBUG', 'INFO', 'WARNING', 'ERROR'];
        if (!validLevels.includes(level)) {
            // Log warning about invalid level to console
            console.warn(`[XPyCode] Invalid log level "${level}", defaulting to DEBUG. Valid levels:`, validLevels);
            level = 'DEBUG';
        }

        // Get caller info
        const callerInfo = this._getCallerInfo(4);
        
        // Build message string from all arguments
        const messagesStr = messages.map(m => {
            if (typeof m === 'object') {
                try {
                    return JSON.stringify(m);
                } catch (e) {
                    return String(m);
                }
            }
            return String(m);
        });

        const messsagesPrefixed = [...messages];
        messsagesPrefixed[0] = `[XPyCode] ${JSON.stringify(messsagesPrefixed[0])}`;

        const messageStr = messagesStr.join(' ');

        // Log to browser console first with caller reference
        const consoleMessage = `[XPyCode] ${messageStr}`;
        const consoleWithCaller = `${consoleMessage}\n    at ${callerInfo}`;

        const messagesWithCaller = [...messsagesPrefixed,'\n', callerInfo]

        switch (level) {
            case 'ERROR':
                console.error(...messagesWithCaller);
                break;
            case 'WARNING':
                console.warn(...messagesWithCaller);
                break;
            case 'DEBUG':
                console.debug(...messagesWithCaller);
                break;
            case 'INFO':
            default:
                console.log(...messagesWithCaller);
                break;
        }
        
        const loggingLevel = (window.XPYCODE_CONFIG && window.XPYCODE_CONFIG.loggingLevel) || 'INFO';
        if (isLoggingLevelEnabled(level, loggingLevel)) {
            // Send to server
            try {
                this.sendRaw({
                    type: 'log_entry',
                    level: level,
                    messages: messagesStr,
                    caller: callerInfo,
                    timestamp: new Date().toISOString()
                });
            } catch (err) {
                // Don't use logToServer here to avoid infinite loop
                console.error('[XPyCode] Failed to send log to server:', err);
            }
        }
    }

    /**
     * Main message handler - routes messages to specific handlers
     * @param {MessageEvent} ev - WebSocket message event
     */
    async _onMessage(ev) {
        const env = JSON.parse(ev.data);
        window.logToServer('DEBUG', 'WebSocket message received:', env.type || env.kind, env);

        // Create message handlers with dependencies
        const handlers = createMessageHandlers({
            chunkHandler: this._chunkHandler,
            contextManager: this.ctx,
            sendRaw: (msg) => this.sendRaw(msg),
            currentSettings: window.currentSettings || { autoscroll: true },
            showErrorNotification: window.showErrorNotification || (() => {}),
            eventDispatcher: this.eventDispatcher,
            registerEventHandlerFn: (objectType, objectId, eventName, moduleName, functionName) => 
                this._registerEventHandler(objectType, objectId, eventName, moduleName, functionName),
            unregisterEventHandlerFn: (objectId, eventName) => 
                this._unregisterEventHandler(objectId, eventName),
            scanWorkbookObjectsFn: () => this._scanWorkbookObjects(),
            registerDynamicFunctionsFn: (functions) => this._registerDynamicFunctions(functions),
            storeFunctions: (functions) => { this._customFunctions = functions; },
            handleFunctionResultFn: (msg) => this._handleFunctionResult(msg),
            processMessageFn: (msg) => this._processMessage(msg),
            pendingFunctionRequests: this._pendingFunctionRequests,
            streamingInvocations: this._streamingInvocations,
            onMessageCallback: (msg) => this._onMessage(msg)
        });

        // Handle the message using the appropriate handler
        const handler = handlers[env.type] || handlers[env.kind];
        if (handler) {
            await handler(env);
            return;
        }

        // If no handler found, log warning
        window.logToServer('DEBUG', 'No handler for message type:', env.type || env.kind);
    }

    /**
     * Register dynamic custom functions wrapper
     */
    _registerDynamicFunctions(functions) {
        registerDynamicFunctions(
            functions,
            this._functionModuleMap,
            this._pendingFunctionRequests,
            this._streamingInvocations,
            this.ctx,
            (msg) => this.sendRaw(msg),
            (msg, data) => this.logToServer(msg, data)
        );
    }

    /**
     * Sync persisted functions with the server on startup
     */
    _syncFunctionsOnStartup() {
        syncFunctionsOnStartup(
            (functions) => this._registerDynamicFunctions(functions),
            (msg) => this.sendRaw(msg)
        );
    }

    /**
     * Register dynamic custom functions
     */
    _registerSavedFunctions() {
        const functions = getRegisteredFunctions();
        this._registerDynamicFunctions(functions);
    }

    /**
     * Handle a function result message (wrapper)
     */
    _handleFunctionResult(message) {
        handleFunctionResult(message, this._pendingFunctionRequests, this.ctx);
    }

    /**
     * Process a single message (for batch processing)
     */
    async _processMessage(msg) {
        // Create a fake event and call _onMessage
        await this._onMessage({ data: JSON.stringify(msg) });
    }

    /**
     * Register an event handler
     */
    async _registerEventHandler(objectType, objectId, eventName, moduleName, functionName) {
        if (!this.eventDispatcher) {
            throw new Error('EventDispatcher not initialized');
        }
        
        // Delegate to EventDispatcher which handles the actual registration
        await this.eventDispatcher.registerHandler(objectType, objectId, eventName, moduleName, functionName);
        
        // Update the event config in the workbook
        const { getEventConfigFromWorkbook, saveEventConfigToWorkbook } = await import('../storage/event-config-storage.js');
        const config = await getEventConfigFromWorkbook() || {};
        
        // Ensure the object entry exists in ID-based format
        if (!config[objectId]) {
            config[objectId] = {
                ObjectType: objectType,
                events: {}
            };
        }
        
        // Store event handler with split fields
        config[objectId].events[eventName] = {
            module_name: moduleName,
            function_name: functionName
        };
        
        // Save updated config
        await saveEventConfigToWorkbook(config);
        
        window.logToServer('DEBUG', `Registered handler: ${objectType}[${objectId}].${eventName} -> ${moduleName}.${functionName}`);
    }

    /**
     * Unregister an event handler
     */
    async _unregisterEventHandler(objectId, eventName) {
        if (!this.eventDispatcher) {
            throw new Error('EventDispatcher not initialized');
        }
        
        // Delegate to EventDispatcher
        await this.eventDispatcher.unregisterHandler(objectId, eventName);
        
        // Update the event config in the workbook
        const { getEventConfigFromWorkbook, saveEventConfigToWorkbook } = await import('../storage/event-config-storage.js');
        const config = await getEventConfigFromWorkbook() || {};
        
        if (config[objectId] && config[objectId].events) {
            delete config[objectId].events[eventName];
            
            // Remove object entry if no events remain
            if (Object.keys(config[objectId].events).length === 0) {
                delete config[objectId];
            }
        }
        
        // Save updated config
        await saveEventConfigToWorkbook(config);
        
        window.logToServer('DEBUG', `Unregistered handler: ${objectId}.${eventName}`);
    }

    /**
     * Scan workbook objects
     */
    async _scanWorkbookObjects() {
        return Excel.run(async (context) => {
            // Use office_tools to get the full workbook tree with ID tracking
            const tree = await getWorkbookTree(context);
            return tree;
        });
    }
}
