// XPyCode Workbook Watcher
// Monitors workbook structure changes and notifies the server

/**
 * WorkbookWatcher class
 * Monitors workbook changes including worksheet/table/chart additions, deletions, and renames
 */
export class WorkbookWatcher {
    /**
     * @param {Function} sendRaw - Function to send messages to server
     * @param {Function} scanWorkbookObjects - Function to scan workbook structure
     * @param {Function} checkWorkbookNameChange - Function to check for workbook name changes
     */
    constructor(sendRaw, scanWorkbookObjects, checkWorkbookNameChange) {
        this.sendRaw = sendRaw;
        this.scanWorkbookObjects = scanWorkbookObjects;
        this.checkWorkbookNameChange = checkWorkbookNameChange;
        
        this._watcherInterval = null;
        this._lastWorkbookTree = null;
        this._collectionEventHandlers = new Map(); // Map<collectionType, handlerResult>
    }

    /**
     * Start the background watcher.
     * Registers collection-level event listeners and starts polling.
     */
    start() {
        if (this._watcherInterval) {
            window.logToServer('DEBUG', 'Watcher already running');
            return;
        }

        window.logToServer('DEBUG', 'Starting background watcher');
        
        // Register collection-level event listeners for immediate detection
        this._registerCollectionListeners();
        
        // Start polling
        this._watcherInterval = setInterval(async () => {
            try {
                const currentTree = await this.scanWorkbookObjects();
                
                // Check for workbook name changes
                await this.checkWorkbookNameChange();
                
                // Compare with last state
                if (this._hasTreeChanged(this._lastWorkbookTree, currentTree)) {
                    window.logToServer('DEBUG', 'Workbook structure changed, sending update');
                    this._lastWorkbookTree = currentTree;
                    
                    // Send update to server
                    this.sendRaw({
                        type: 'workbook_structure_update',
                        tree: currentTree
                    });
                }
            } catch (err) {
                window.logToServer('ERROR', 'Error in background watcher:', err);
            }
        }, 3000); // Poll every 3 seconds
        
        // Do initial scan
        this.scanWorkbookObjects().then(tree => {
            this._lastWorkbookTree = tree;
            this.sendRaw({
                type: 'workbook_structure_update',
                tree: tree
            });
        }).catch(err => {
            window.logToServer('ERROR', 'Error in initial scan:', err);
        });
    }

    /**
     * Stop the background watcher.
     */
    stop() {
        if (this._watcherInterval) {
            clearInterval(this._watcherInterval);
            this._watcherInterval = null;
            window.logToServer('DEBUG', 'Stopped background watcher');
        }
        this._unregisterCollectionListeners();
    }

    /**
     * Register collection-level event listeners for immediate structure change detection.
     */
    async _registerCollectionListeners() {
        try {
            await Excel.run(async (context) => {
                const workbook = context.workbook;
                
                // WorksheetCollection events
                const wsHandler = workbook.worksheets.onAdded.add(async () => {
                    window.logToServer('DEBUG', 'Worksheet added, triggering immediate scan');
                    this._triggerImmediateScan();
                });
                this._collectionEventHandlers.set('worksheets_added', wsHandler);
                
                const wsDelHandler = workbook.worksheets.onDeleted.add(async () => {
                    window.logToServer('DEBUG', 'Worksheet deleted, triggering immediate scan');
                    this._triggerImmediateScan();
                });
                this._collectionEventHandlers.set('worksheets_deleted', wsDelHandler);
                
                const wsNameHandler = workbook.worksheets.onNameChanged.add(async () => {
                    window.logToServer('DEBUG', 'Worksheet renamed, triggering immediate scan');
                    this._triggerImmediateScan();
                });
                this._collectionEventHandlers.set('worksheets_nameChanged', wsNameHandler);
                
                // TableCollection events
                const tableHandler = workbook.tables.onAdded.add(async () => {
                    window.logToServer('DEBUG', 'Table added, triggering immediate scan');
                    this._triggerImmediateScan();
                });
                this._collectionEventHandlers.set('tables_added', tableHandler);
                
                const tableDelHandler = workbook.tables.onDeleted.add(async () => {
                    window.logToServer('DEBUG', 'Table deleted, triggering immediate scan');
                    this._triggerImmediateScan();
                });
                this._collectionEventHandlers.set('tables_deleted', tableDelHandler);
                
                await context.sync();
                window.logToServer('DEBUG', 'Collection event listeners registered');
            });
        } catch (err) {
            window.logToServer('ERROR', 'Error registering collection listeners:', err);
        }
    }

    /**
     * Unregister collection-level event listeners.
     */
    async _unregisterCollectionListeners() {
        if (this._collectionEventHandlers.size === 0) return;
        
        try {
            await Excel.run(async (context) => {
                for (const [key, handler] of this._collectionEventHandlers.entries()) {
                    try {
                        handler.remove();
                        window.logToServer('DEBUG', `Removed collection listener: ${key}`);
                    } catch (err) {
                        window.logToServer('WARNING', `Error removing listener ${key}:`, err);
                    }
                }
                await context.sync();
            });
            this._collectionEventHandlers.clear();
        } catch (err) {
            window.logToServer('ERROR', 'Error unregistering collection listeners:', err);
        }
    }

    /**
     * Trigger an immediate scan of the workbook structure.
     * This is called when collection events fire.
     */
    async _triggerImmediateScan() {
        try {
            const currentTree = await this.scanWorkbookObjects();
            
            // Always send update on immediate scan (events are high-confidence changes)
            this._lastWorkbookTree = currentTree;
            
            this.sendRaw({
                type: 'workbook_structure_update',
                tree: currentTree
            });
        } catch (err) {
            window.logToServer('ERROR', 'Error in immediate scan:', err);
        }
    }

    /**
     * Compare two workbook trees to detect changes.
     * Compares by object IDs, types, and names.
     * 
     * @param {Object} oldTree - Previous tree state
     * @param {Object} newTree - Current tree state
     * @returns {boolean} True if trees are different
     */
    _hasTreeChanged(oldTree, newTree) {
        if (!oldTree) return true;
        if (!newTree) return false;
        
        // Convert trees to comparable strings (using object IDs)
        const oldStr = this._treeToString(oldTree);
        const newStr = this._treeToString(newTree);
        
        return oldStr !== newStr;
    }

    /**
     * Convert a tree to a comparable string representation.
     * Uses object IDs, types, and names for comparison.
     */
    _treeToString(node) {
        if (!node) return '';
        
        const parts = [node.type, node.id, node.name];
        
        if (node.children && node.children.length > 0) {
            const childStrs = node.children
                .map(child => this._treeToString(child))
                .join('|');
            parts.push(childStrs);
        }
        
        return parts.join(':');
    }
}
