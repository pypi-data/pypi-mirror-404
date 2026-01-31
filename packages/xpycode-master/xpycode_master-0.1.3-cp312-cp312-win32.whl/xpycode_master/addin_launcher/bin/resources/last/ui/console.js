// XPyCode UI Console Module
// Manages the Python console UI display

import { getSetting } from '../settings/index.js';

/**
 * PythonCodeConsole class
 * Handles the console output display in the taskpane
 */
export class PythonCodeConsole {
    constructor() {
        this.statusIndicator = null;
        this.consoleOutput = null;
    }

    init() {
        this.statusIndicator = document.getElementById('status-indicator');
        this.consoleOutput = document.getElementById('console-output');
    }

    setConnected(isConnected) {
        if (!this.statusIndicator) return;
        if (isConnected) {
            this.statusIndicator.className = 'status-connected';
            this.statusIndicator.textContent = 'Connected';
        } else {
            this.statusIndicator.className = 'status-disconnected';
            this.statusIndicator.textContent = 'Disconnected';
        }
    }

    setStatus(message, type = 'info') {
        if (!this.statusIndicator) return;
        this.statusIndicator.textContent = message;
        if (type === 'error') {
            this.statusIndicator.className = 'status-disconnected';
        } else if (type === 'warning') {
            this.statusIndicator.className = 'status-connecting';
        } else {
            this.statusIndicator.className = 'status-connected';
        }
    }

    log(message, type = 'info') {
        if (!this.consoleOutput) return;
        const timestamp = new Date().toLocaleTimeString();
        const prefix = type === 'error' ? '[Error] ' : '';
        this.consoleOutput.textContent += '[' + timestamp + '] ' + prefix + message + '\n';
        // Scroll to bottom if autoscroll is enabled
        if (getSetting('autoscroll')) {
            this.consoleOutput.scrollTop = this.consoleOutput.scrollHeight;
        }
    }

    clear() {
        if (!this.consoleOutput) return;
        this.consoleOutput.textContent = '';
    }
}

/**
 * Helper function to append content to console
 * Consolidates stdout/stderr handling logic
 * @param {string} content - Content to append
 * @param {Object} options - Options for appending
 * @param {boolean} options.isError - Whether this is error content (red text)
 * @param {Object} options.limits - Console limits configuration
 * @param {Object} options.state - Mutable state object for tracking append count
 */
export function appendToConsole(content, options = {}) {
    const { isError = false, limits = {}, state = {} } = options;
    
    try {
        const consoleOutput = document.getElementById('console-output');
        if (!consoleOutput) return;

        // Create a span element for the content
        const span = document.createElement('span');
        if (isError) {
            span.style.color = 'red';
        }
        span.textContent = content;
        consoleOutput.appendChild(span);

        // Limit console output to prevent memory issues
        if (state && typeof state.appendCount === 'number' && limits.checkInterval) {
            state.appendCount++;

            if (state.appendCount % limits.checkInterval === 0) {
                // Use character length as proxy to avoid expensive split on every check
                if (consoleOutput.textContent.length > limits.maxChars) {
                    // Count newlines efficiently before doing expensive split
                    const newlineMatches = consoleOutput.textContent.match(/\n/g);
                    const lineCount = newlineMatches ? newlineMatches.length + 1 : 1;

                    if (lineCount > limits.maxLines) {
                        // Keep only the most recent lines
                        // Note: This replaces DOM with plain text, losing span styling
                        // This is acceptable for performance when trimming very large output
                        const lines = consoleOutput.textContent.split('\n');
                        consoleOutput.textContent = '';
                        consoleOutput.insertAdjacentText('beforeend', lines.slice(-limits.trimToLines).join('\n'));
                    }
                }
            }
        }

        // Scroll to bottom to show latest output if autoscroll is enabled
        if (getSetting('autoscroll')) {
            consoleOutput.scrollTop = consoleOutput.scrollHeight;
        }
    } catch (err) {
        window.logToServer('ERROR', 'Error appending to console:', err);
    }
}
