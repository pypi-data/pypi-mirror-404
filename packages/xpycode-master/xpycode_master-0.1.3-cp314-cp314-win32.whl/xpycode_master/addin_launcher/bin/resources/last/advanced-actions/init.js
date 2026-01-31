// Initialize advanced actions module

import { initAdvancedActionsDialog, openAdvancedActionsDialog } from './advanced-actions-dialog.js';
import { initConfirmDialog } from './confirm-dialog.js';
import { ADVANCED_ACTIONS_CONFIG } from './actions-config.js';

/**
 * Initialize the advanced actions module
 */
export function initAdvancedActions() {
    initConfirmDialog();
    initAdvancedActionsDialog(ADVANCED_ACTIONS_CONFIG);
    
    // Setup button click handler
    const advancedBtn = document.getElementById('advanced-actions-btn');
    if (advancedBtn) {
        advancedBtn.addEventListener('click', openAdvancedActionsDialog);
    }
}
