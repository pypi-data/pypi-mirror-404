// XPyCode Binding Manager Module
// Core binding CRUD operations

import { capitalizeFirst, escapeHtml } from '../utils/index.js';
import { showMessageDialog } from '../utils/index.js';

// Store for existing binding IDs (for validation)
export let existingBindingIds = new Set();

// Binding name validation pattern
export const BINDING_NAME_PATTERN = /^[a-zA-Z_][a-zA-Z0-9_-]*$/;

/**
 * Get all bindings from Office
 * @returns {Promise<Array>} Array of binding objects
 */
export function getAllBindings() {
    return new Promise((resolve, reject) => {
        Office.context.document.bindings.getAllAsync((result) => {
            if (result.status === Office.AsyncResultStatus.Succeeded) {
                resolve(result.value);
            } else {
                reject(result.error);
            }
        });
    });
}

/**
 * Refresh the set of existing binding IDs
 */
export async function refreshExistingBindingIds() {
    existingBindingIds.clear();
    
    try {
        const bindings = await getAllBindings();
        bindings.forEach(b => existingBindingIds.add(b.id));
    } catch (error) {
        window.logToServer('ERROR', 'Error fetching existing bindings:', error);
    }
}

/**
 * Create a new binding
 * @param {string} name - Binding name
 * @param {string} bindingType - Type of binding (range, table, text)
 * @returns {Promise<void>}
 */
export async function createBinding(name, bindingType) {
    // Map type to Office binding type
    const bindingTypeMap = {
        'range': Office.BindingType.Matrix,
        'table': Office.BindingType.Table,
        'text': Office.BindingType.Text
    };
    
    const officeBindingType = bindingTypeMap[bindingType];
    const typeLabel = capitalizeFirst(bindingType);
    
    try {
        await new Promise((resolve, reject) => {
            Office.context.document.bindings.addFromPromptAsync(
                officeBindingType,
                {
                    id: name,
                    promptText: `Select a ${bindingType} to bind as "${name}"`
                },
                (result) => {
                    if (result.status === Office.AsyncResultStatus.Succeeded) {
                        resolve(result.value);
                    } else {
                        reject(result.error);
                    }
                }
            );
        });
        
        showMessageDialog('Success', `Binding "${name}" created successfully!`);
        
    } catch (error) {
        if (error.code === Office.ErrorCodes.OperationCancelled || 
            error.message?.includes('cancel')) {
            showMessageDialog('Cancelled', 'Binding creation was cancelled.');
        } else {
            showMessageDialog('Error', `Failed to create binding: ${error.message}`);
        }
    }
}

/**
 * Delete a binding by ID
 * @param {string} bindingId - ID of binding to delete
 * @returns {Promise<void>}
 */
export async function deleteBinding(bindingId) {
    try {
        await new Promise((resolve, reject) => {
            Office.context.document.bindings.releaseByIdAsync(bindingId, (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    resolve();
                } else {
                    reject(result.error);
                }
            });
        });
    } catch (error) {
        showMessageDialog('Error', `Failed to delete binding: ${error.message}`);
        throw error;
    }
}

/**
 * Get binding reference (Excel range address or table name)
 * @param {Object} binding - Binding object
 * @returns {Promise<string>} Reference string
 */
export async function getBindingReference(binding) {
    // Check if Excel is available
    if (typeof Excel === 'undefined') {
        return binding.id;
    }
    
    // Try to get range address using Excel API
    try {
        return await Excel.run(async (context) => {
            const excelBinding = context.workbook.bindings.getItem(binding.id);
            
            // For table bindings, get the table reference
            if (binding.type.toLowerCase() === 'table') {
                const table = excelBinding.getTable();
                table.load('name');
                await context.sync();
                return `Table: ${table.name}`;
            } else {
                // For matrix/range bindings
                const range = excelBinding.getRange();
                range.load('address');
                await context.sync();
                return range.address;
            }
        });
    } catch (e) {
        // Fallback for non-Excel or if Excel API fails
        return binding.id;
    }
}

/**
 * Get text binding content preview
 * @param {Object} binding - Binding object
 * @returns {Promise<string>} Preview text
 */
export async function getBindingTextPreview(binding) {
    return new Promise((resolve) => {
        binding.getDataAsync({ 
            valueFormat: Office.ValueFormat.Unformatted 
        }, (result) => {
            if (result.status === Office.AsyncResultStatus.Succeeded) {
                const text = String(result.value);
                // Truncate if too long
                resolve(text.length > 30 ? text.substring(0, 30) + '...' : text);
            } else {
                resolve('(unable to read)');
            }
        });
    });
}

/**
 * Validate binding name
 * @param {string} name - Name to validate
 * @returns {Object} Validation result {valid: boolean, message: string}
 */
export function validateBindingName(name) {
    // Check if empty
    if (!name) {
        return { valid: false, message: '' };
    }
    
    // Check if valid ID (alphanumeric, underscore, hyphen, no spaces at start)
    if (!BINDING_NAME_PATTERN.test(name)) {
        return { 
            valid: false, 
            message: 'Invalid name. Use letters, numbers, underscores, hyphens. Must start with a letter or underscore.' 
        };
    }
    
    // Check for duplicates
    if (existingBindingIds.has(name)) {
        return { 
            valid: false, 
            message: 'A binding with this name already exists.' 
        };
    }
    
    // Valid
    return { valid: true, message: '' };
}

/**
 * Build HTML for a collapsible tree node
 * @param {string} icon - Emoji icon
 * @param {string} title - Section title (e.g., "Range Bindings")
 * @param {Array} bindings - Array of binding objects with id and reference
 * @param {boolean} startExpanded - Whether to start expanded (default: true if has items)
 * @returns {string} HTML string
 */
export function buildTreeNode(icon, title, bindings, startExpanded = null) {
    const count = bindings.length;
    const isEmpty = count === 0;
    const isExpanded = startExpanded !== null ? startExpanded : !isEmpty;
    
    const collapsedClass = isExpanded ? '' : 'collapsed';
    const emptyClass = isEmpty ? 'empty' : '';
    
    let html = `
        <div class="tree-node ${collapsedClass} ${emptyClass}">
            <div class="tree-node-header">
                <svg class="tree-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
                <span class="tree-node-title">${icon} ${escapeHtml(title)} <span class="tree-node-count">(${count})</span></span>
            </div>
            <div class="tree-node-content">
    `;
    
    if (isEmpty) {
        html += `<div class="tree-empty-message">No bindings</div>`;
    } else {
        for (const binding of bindings) {
            html += `
                <div class="tree-binding-item">
                    <span class="tree-binding-id">${escapeHtml(binding.id)}</span>
                    <span class="tree-binding-reference">${escapeHtml(binding.reference)}</span>
                    <button class="tree-binding-delete" data-binding-id="${escapeHtml(binding.id)}" title="Delete binding">
                        <svg viewBox="0 0 24 24" width="16" height="16">
                            <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z" 
                                  stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
                            <line x1="10" y1="11" x2="10" y2="17" stroke="currentColor" stroke-width="2"/>
                            <line x1="14" y1="11" x2="14" y2="17" stroke="currentColor" stroke-width="2"/>
                        </svg>
                    </button>
                </div>
            `;
        }
    }
    
    html += `
            </div>
        </div>
    `;
    
    return html;
}

/**
 * Build HTML section for a group of bindings
 * @deprecated Use buildTreeNode instead
 * @param {string} title - Section title
 * @param {Array} bindings - Array of binding objects with id and reference
 * @returns {string} HTML string
 */
export function buildBindingSection(title, bindings) {
    let html = `
        <div class="bindings-section">
            <div class="bindings-section-title">${title}</div>
            <div class="bindings-list">
    `;
    
    for (const binding of bindings) {
        html += `
            <div class="binding-item">
                <span class="binding-id">${escapeHtml(binding.id)}</span>
                <span class="binding-reference">${escapeHtml(binding.reference)}</span>
                <button class="binding-delete" data-binding-id="${escapeHtml(binding.id)}" title="Delete binding">
                    <svg viewBox="0 0 24 24" width="16" height="16">
                        <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z" 
                              stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
                        <line x1="10" y1="11" x2="10" y2="17" stroke="currentColor" stroke-width="2"/>
                        <line x1="14" y1="11" x2="14" y2="17" stroke="currentColor" stroke-width="2"/>
                    </svg>
                </button>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    return html;
}

/**
 * Load and display bindings list in manage dialog as a tree view
 * @returns {Promise<HTMLElement>} The container element
 */
export async function loadBindingsList() {
    const container = document.getElementById('manage-bindings-content');
    container.innerHTML = '<div class="bindings-loading">Loading bindings...</div>';
    
    try {
        const bindings = await getAllBindings();
        
        // Group bindings by type
        const grouped = {
            matrix: [],  // Range bindings
            table: [],
            text: []
        };
        
        for (const binding of bindings) {
            const type = binding.type.toLowerCase();
            if (grouped[type]) {
                // Get reference info
                let reference = '';
                try {
                    if (type === 'matrix' || type === 'table') {
                        // For Excel, try to get the range address
                        reference = await getBindingReference(binding);
                    } else if (type === 'text') {
                        // For text, show preview of content
                        reference = await getBindingTextPreview(binding);
                    }
                } catch (e) {
                    reference = '(unable to get reference)';
                }
                
                grouped[type].push({
                    id: binding.id,
                    reference: reference
                });
            }
        }
        
        // Build tree HTML
        let html = '<div class="bindings-tree">';
        html += buildTreeNode('📊', 'Range Bindings', grouped.matrix);
        html += buildTreeNode('📋', 'Table Bindings', grouped.table);
        html += buildTreeNode('📝', 'Text Bindings', grouped.text);
        html += '</div>';
        
        container.innerHTML = html;
        
        // Add expand/collapse handlers for tree node headers
        container.querySelectorAll('.tree-node-header').forEach(header => {
            header.addEventListener('click', () => {
                const node = header.closest('.tree-node');
                if (!node.classList.contains('empty')) {
                    node.classList.toggle('collapsed');
                }
            });
        });
        
        // Return container for dialog to add event handlers
        return container;
        
    } catch (error) {
        container.innerHTML = `<div class="bindings-empty">Error loading bindings: ${error.message}</div>`;
    }
}
