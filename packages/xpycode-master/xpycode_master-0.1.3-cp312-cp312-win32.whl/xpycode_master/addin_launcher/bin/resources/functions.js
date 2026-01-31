// This file contains all custom function implementations

// Store for dynamically registered functions
const registeredFunctions = {};

/**
 * Generic handler that routes to dynamically registered functions
 */
function dynamicFunctionHandler(functionId, ... args) {
  if (registeredFunctions[functionId]) {
    return registeredFunctions[functionId](...args);
  }
  return `#ERROR: Function ${functionId} not found`;
}

/**
 * Register a new function implementation
 */
function registerFunctionImplementation(functionId, implementation) {
  registeredFunctions[functionId] = implementation;
  CustomFunctions.associate(functionId, (...args) => dynamicFunctionHandler(functionId, ...args));
}

// Expose for use from taskpane
window.registerFunctionImplementation = registerFunctionImplementation;

