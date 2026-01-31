// XPyCode Binding Dialogs Module
// Dialog management for binding operations

import { 
    refreshExistingBindingIds, 
    createBinding, 
    deleteBinding, 
    validateBindingName,
    loadBindingsList 
} from './binding-manager.js';
import { capitalizeFirst } from '../utils/index.js';

// Current binding type being created
let currentBindingType = null;

// Binding ID pending deletion
let pendingDeleteBindingId = null;

/**
 * Initialize binding dropdown
 */
export function initBindingDropdown() {
    const dropdownToggle = document.querySelector('#binding-dropdown .dropdown-toggle');
    const dropdownMenu = document.getElementById('binding-menu');
    
    if (!dropdownToggle || !dropdownMenu) return;
    
    // Toggle dropdown on click
    dropdownToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownMenu.classList.toggle('show');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
        dropdownMenu.classList.remove('show');
    });
    
    // Handle menu item clicks
    dropdownMenu.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (!action) return;
        
        dropdownMenu.classList.remove('show');
        
        switch (action) {
            case 'new-range':
                openNewBindingDialog('range');
                break;
            case 'new-table':
                openNewBindingDialog('table');
                break;
            case 'new-text':
                openNewBindingDialog('text');
                break;
            case 'manage':
                openManageBindingsDialog();
                break;
        }
    });
}

// ==================== NEW BINDING DIALOG ====================

/**
 * Open new binding dialog
 * @param {string} type - Binding type (range, table, text)
 */
export async function openNewBindingDialog(type) {
    currentBindingType = type;
    
    // Fetch existing bindings for validation
    await refreshExistingBindingIds();
    
    // Update dialog title and button text
    const typeLabel = capitalizeFirst(type);
    document.getElementById('new-binding-title').textContent = `New ${typeLabel} Binding`;
    document.getElementById('binding-select-btn').textContent = `Select ${typeLabel}`;
    
    // Reset input
    const input = document.getElementById('binding-name-input');
    input.value = '';
    input.classList.remove('invalid');
    document.getElementById('binding-validation-message').textContent = '';
    document.getElementById('binding-select-btn').disabled = true;
    
    // Show dialog
    document.getElementById('new-binding-dialog').style.display = 'flex';
    input.focus();
}

/**
 * Close new binding dialog
 */
export function closeNewBindingDialog() {
    document.getElementById('new-binding-dialog').style.display = 'none';
    currentBindingType = null;
}

/**
 * Handle binding name validation in UI
 */
function handleBindingNameValidation() {
    const input = document.getElementById('binding-name-input');
    const selectBtn = document.getElementById('binding-select-btn');
    const validationMsg = document.getElementById('binding-validation-message');
    
    const name = input.value.trim();
    const result = validateBindingName(name);
    
    if (!name) {
        input.classList.remove('invalid');
        validationMsg.textContent = '';
        selectBtn.disabled = true;
        return false;
    }
    
    if (!result.valid) {
        input.classList.add('invalid');
        validationMsg.textContent = result.message;
        selectBtn.disabled = true;
        return false;
    }
    
    // Valid
    input.classList.remove('invalid');
    validationMsg.textContent = '';
    selectBtn.disabled = false;
    return true;
}

/**
 * Handle create binding button click
 */
async function handleCreateBinding() {
    const name = document.getElementById('binding-name-input').value.trim();
    
    if (!handleBindingNameValidation()) {
        return;
    }
    
    const workingBindingType = currentBindingType;
    closeNewBindingDialog();

    // Validate currentBindingType
    if (!workingBindingType || !['range', 'table', 'text'].includes(workingBindingType)) {
        const { showMessageDialog } = await import('../utils/index.js');
        showMessageDialog('Error', 'Invalid binding type.');
        return;
    }
    
    await createBinding(name, workingBindingType);
}

/**
 * Initialize new binding dialog event handlers
 */
export function initNewBindingDialog() {
    const input = document.getElementById('binding-name-input');
    const selectBtn = document.getElementById('binding-select-btn');
    const cancelBtn = document.getElementById('binding-cancel-btn');
    const closeBtn = document.getElementById('new-binding-close');
    
    if (!input || !selectBtn || !cancelBtn || !closeBtn) return;
    
    // Validate on input
    input.addEventListener('input', handleBindingNameValidation);
    
    // Select button
    selectBtn.addEventListener('click', handleCreateBinding);
    
    // Cancel/Close buttons
    cancelBtn.addEventListener('click', closeNewBindingDialog);
    closeBtn.addEventListener('click', closeNewBindingDialog);
    
    // Close on overlay click
    document.getElementById('new-binding-dialog').addEventListener('click', (e) => {
        if (e.target.classList.contains('dialog-overlay')) {
            closeNewBindingDialog();
        }
    });
}

// ==================== MANAGE BINDINGS DIALOG ====================

/**
 * Attach delete button handlers to tree binding items
 * @param {HTMLElement} container - The container element with binding items
 */
function attachDeleteHandlers(container) {
    if (!container) return;
    
    container.querySelectorAll('.tree-binding-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering the collapse/expand
            const bindingId = btn.dataset.bindingId;
            openDeleteConfirmDialog(bindingId);
        });
    });
}

/**
 * Open manage bindings dialog
 */
export async function openManageBindingsDialog() {
    document.getElementById('manage-bindings-dialog').style.display = 'flex';
    const container = await loadBindingsList();
    attachDeleteHandlers(container);
}

/**
 * Close manage bindings dialog
 */
export function closeManageBindingsDialog() {
    document.getElementById('manage-bindings-dialog').style.display = 'none';
}

/**
 * Initialize manage bindings dialog event handlers
 */
export function initManageBindingsDialog() {
    const closeBtn = document.getElementById('manage-bindings-close');
    const doneBtn = document.getElementById('manage-bindings-done');
    
    if (!closeBtn || !doneBtn) return;
    
    closeBtn.addEventListener('click', closeManageBindingsDialog);
    doneBtn.addEventListener('click', closeManageBindingsDialog);
    
    // Close on overlay click
    document.getElementById('manage-bindings-dialog').addEventListener('click', (e) => {
        if (e.target.classList.contains('dialog-overlay')) {
            closeManageBindingsDialog();
        }
    });
}

// ==================== DELETE CONFIRMATION DIALOG ====================

/**
 * Open delete confirmation dialog
 * @param {string} bindingId - ID of binding to delete
 */
export function openDeleteConfirmDialog(bindingId) {
    pendingDeleteBindingId = bindingId;
    document.getElementById('delete-binding-name').textContent = bindingId;
    document.getElementById('delete-confirm-dialog').style.display = 'flex';
}

/**
 * Close delete confirmation dialog
 */
export function closeDeleteConfirmDialog() {
    document.getElementById('delete-confirm-dialog').style.display = 'none';
    pendingDeleteBindingId = null;
}

/**
 * Handle delete binding confirmation
 */
async function handleDeleteBinding() {
    const bindingId = pendingDeleteBindingId;
    closeDeleteConfirmDialog();
    
    if (!bindingId) return;
    
    try {
        await deleteBinding(bindingId);
        // Refresh the bindings list and re-attach handlers
        const container = await loadBindingsList();
        attachDeleteHandlers(container);
    } catch (error) {
        // Error already shown in deleteBinding
    }
}

/**
 * Initialize delete confirmation dialog event handlers
 */
export function initDeleteConfirmDialog() {
    const yesBtn = document.getElementById('delete-confirm-yes');
    const cancelBtn = document.getElementById('delete-confirm-cancel');
    
    if (!yesBtn || !cancelBtn) return;
    
    yesBtn.addEventListener('click', handleDeleteBinding);
    cancelBtn.addEventListener('click', closeDeleteConfirmDialog);
    
    // Close on overlay click
    document.getElementById('delete-confirm-dialog').addEventListener('click', (e) => {
        if (e.target.classList.contains('dialog-overlay')) {
            closeDeleteConfirmDialog();
        }
    });
}
