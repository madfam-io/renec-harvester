// Prevent browser extensions from modifying the DOM during hydration
(function() {
  'use strict';
  
  // Store original methods
  const originalSetAttribute = Element.prototype.setAttribute;
  const originalStyle = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'style');
  
  // Block VS Code extension style injection
  Element.prototype.setAttribute = function(name, value) {
    if (name === 'style' && typeof value === 'string' && value.includes('--vsc-')) {
      return;
    }
    return originalSetAttribute.call(this, name, value);
  };
  
  // Prevent direct style property access
  Object.defineProperty(HTMLElement.prototype, 'style', {
    get: function() {
      return originalStyle.get.call(this);
    },
    set: function(value) {
      if (typeof value === 'string' && value.includes('--vsc-')) {
        return;
      }
      return originalStyle.set.call(this, value);
    }
  });
  
  // Clean up any existing extension styles
  document.addEventListener('DOMContentLoaded', function() {
    const elements = document.querySelectorAll('[style*="--vsc-"]');
    elements.forEach(el => {
      el.removeAttribute('style');
    });
  });
})();