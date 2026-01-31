// String utility functions

/**
 * Capitalize the first letter of a string
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 */
export function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Escape HTML special characters to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

export function isLoggingLevelEnabled(level, loggingLevel) {
    const levels = ['ERROR', 'WARNING', 'INFO', 'DEBUG'];
    const levelIndex = levels.indexOf(level);
    const loggingLevelIndex = levels.indexOf(loggingLevel);
    return levelIndex <= loggingLevelIndex;
} 
