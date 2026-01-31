// XPyCode Constants
// All constants used across the add-in

// Special parent ID indicating a temporary/event object that doesn't have a full object model path
export const TEMPORARY_PARENT_ID = -1;

// UDF function execution timeout (milliseconds)
export const UDF_EXECUTION_TIMEOUT_MS = 30000;

// Invalid function ID returned when sanitization fails
export const INVALID_FUNCTION_ID = 'INVALIDFUNCTION';

// Console limits (defined in Messaging class but extracted here)
export const CONSOLE_CHECK_INTERVAL = 100;        // Check for trimming every N appends
export const CONSOLE_MAX_CHARS = 800000;          // ~800KB (~10K lines at 80 chars/line)
export const CONSOLE_MAX_LINES = 10000;           // Maximum lines before trimming
export const CONSOLE_TRIM_TO_LINES = 8000;        // Lines to keep after trimming

// Notification settings
export const NOTIFICATION_THROTTLE_MS = 500;     // 5 seconds between notifications
export const ERROR_MESSAGE_TRUNCATE_LENGTH = 50;  // Characters to show in error indicator
export const ERROR_INDICATOR_AUTO_HIDE_MS = 10000; // 10 seconds
export const DOM_RENDER_DELAY_MS = 100;           // Delay to wait for DOM rendering
