// Advanced Actions Dialog - Generic multi-tab action dialog

import { showConfirmDialog } from './confirm-dialog.js';
import { showMessageDialog } from '../utils/dialog-utils.js';

let currentTab = null;
let actionsConfig = null;

/**
 * Initialize the advanced actions dialog
 * @param {Map} config - Map of tab_name -> actions array
 */
export function initAdvancedActionsDialog(config) {
    actionsConfig = config;
    
    const dialog = document.getElementById('advanced-actions-dialog');
    const closeBtn = document.getElementById('advanced-actions-close');
    const doneBtn = document.getElementById('advanced-actions-done');
    
    if (!dialog || !closeBtn || !doneBtn) return;
    
    closeBtn.addEventListener('click', closeAdvancedActionsDialog);
    doneBtn.addEventListener('click', closeAdvancedActionsDialog);
    
    // Close on overlay click
    dialog.addEventListener('click', (e) => {
        if (e.target.classList.contains('dialog-overlay')) {
            closeAdvancedActionsDialog();
        }
    });
    
    // Build tabs
    buildTabs();
}

/**
 * Build the tab buttons from config
 */
function buildTabs() {
    const tabsContainer = document.getElementById('advanced-actions-tabs');
    if (!tabsContainer || !actionsConfig) return;
    
    tabsContainer.innerHTML = '';
    
    let isFirst = true;
    for (const [tabName, actions] of actionsConfig) {
        const tabBtn = document.createElement('button');
        tabBtn.className = 'tab-btn' + (isFirst ? ' active' : '');
        tabBtn.textContent = tabName;
        tabBtn.dataset.tab = tabName;
        tabBtn.addEventListener('click', () => selectTab(tabName));
        tabsContainer.appendChild(tabBtn);
        
        if (isFirst) {
            currentTab = tabName;
            isFirst = false;
        }
    }
}

/**
 * Select a tab and show its content
 * @param {string} tabName - The tab to select
 */
function selectTab(tabName) {
    currentTab = tabName;
    
    // Update tab button states
    const tabBtns = document.querySelectorAll('#advanced-actions-tabs .tab-btn');
    tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Build content for selected tab
    buildTabContent(tabName);
}

/**
 * Build the content for a specific tab
 * @param {string} tabName - The tab name
 */
function buildTabContent(tabName) {
    const contentContainer = document.getElementById('advanced-actions-content');
    if (!contentContainer || !actionsConfig) return;
    
    const actions = actionsConfig.get(tabName);
    if (!actions) {
        contentContainer.innerHTML = '<div class="actions-empty">No actions available</div>';
        return;
    }
    
    let html = '<div class="actions-list">';
    
    actions.forEach((action, index) => {
        const inputId = `action-input-${tabName}-${index}`;
        html += `
            <div class="action-item" data-tab="${tabName}" data-index="${index}">
                <div class="action-info">
                    <span class="action-description">${escapeHtml(action.description)}</span>
                </div>
                ${action.hasInput ? `
                    <div class="action-input-container">
                        <input type="text" class="action-input dialog-input" id="${inputId}" 
                               placeholder="Enter value..." autocomplete="off">
                    </div>
                ` : ''}
                <div class="action-button-container">
                    <button class="dialog-btn action-execute-btn" data-action-index="${index}">
                        ${escapeHtml(action.shortName)}
                    </button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    contentContainer.innerHTML = html;
    
    // Add event listeners for execute buttons
    contentContainer.querySelectorAll('.action-execute-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const index = parseInt(btn.dataset.actionIndex);
            executeAction(tabName, index);
        });
    });
}

/**
 * Execute an action with confirmation
 * @param {string} tabName - The tab name
 * @param {number} actionIndex - The action index
 */
async function executeAction(tabName, actionIndex) {
    const actions = actionsConfig.get(tabName);
    if (!actions || !actions[actionIndex]) return;
    
    const action = actions[actionIndex];
    
    // Get input value if action has input
    let inputValue = null;
    if (action.hasInput) {
        const inputId = `action-input-${tabName}-${actionIndex}`;
        const inputEl = document.getElementById(inputId);
        inputValue = inputEl ? inputEl.value.trim() : '';
        
        if (!inputValue) {
            showMessageDialog('Validation Error', 'Please enter a value');
            return;
        }
    }
    
    // Show confirmation dialog
    const confirmed = await showConfirmDialog(
        'Confirm Action',
        `Are you sure you want to execute "${action.shortName}"?`
    );
    
    if (!confirmed) return;
    
    // Execute the action
    try {
        let success;
        if (action.hasInput) {
            success = action.actionFunction(inputValue);
        } else {
            success = action.actionFunction();
        }
        
        // Check if action reported failure (e.g., not connected)
        if (success === false) {
            showMessageDialog('Action Failed', 'Unable to execute action. Please ensure you are connected to the business layer.');
        } else {
            window.logToServer('DEBUG', `Action "${action.shortName}" executed successfully`);
        }
    } catch (error) {
        window.logToServer('ERROR', `Error executing action "${action.shortName}":`, error);
        showMessageDialog('Error', `Error executing action: ${error.message}`);
    }
}

/**
 * Open the advanced actions dialog
 */
export function openAdvancedActionsDialog() {
    const dialog = document.getElementById('advanced-actions-dialog');
    if (!dialog) return;
    
    dialog.style.display = 'flex';
    
    // Select first tab and build content
    if (actionsConfig && actionsConfig.size > 0) {
        const firstTab = actionsConfig.keys().next().value;
        selectTab(firstTab);
    }
}

/**
 * Close the advanced actions dialog
 */
export function closeAdvancedActionsDialog() {
    const dialog = document.getElementById('advanced-actions-dialog');
    if (dialog) {
        dialog.style.display = 'none';
    }
}

/**
 * Escape HTML special characters
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
