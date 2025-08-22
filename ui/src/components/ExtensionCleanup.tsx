'use client'

import { useEffect } from 'react'

export default function ExtensionCleanup() {
  useEffect(() => {
    // Clean up VS Code extension styles
    const cleanupExtensionStyles = () => {
      const html = document.documentElement
      const body = document.body
      
      // Remove style attribute if it contains VS Code properties
      const elements = [html]
      if (body) {
        elements.push(body)
      }
      
      elements.forEach(element => {
        if (element) {
          const style = element.getAttribute('style')
          if (style && style.includes('--vsc-')) {
            element.removeAttribute('style')
          }
        }
      })
      
      // Also clean computed styles
      const htmlStyle = html.style
      if (htmlStyle) {
        for (let i = htmlStyle.length - 1; i >= 0; i--) {
          const prop = htmlStyle[i]
          if (prop.startsWith('--vsc-')) {
            htmlStyle.removeProperty(prop)
          }
        }
      }
    }
    
    // Run immediately
    cleanupExtensionStyles()
    
    // Run again after a short delay to catch late injections
    const timeouts = [0, 10, 100, 500].map(delay => 
      setTimeout(cleanupExtensionStyles, delay)
    )
    
    // Set up mutation observer to catch any new injections
    const observer = new MutationObserver(() => {
      cleanupExtensionStyles()
    })
    
    // Observe both html and body elements
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['style'],
      attributeOldValue: true
    })
    
    // Also observe body when it becomes available
    const observeBody = () => {
      if (document.body && !document.body.hasAttribute('data-observer-attached')) {
        document.body.setAttribute('data-observer-attached', 'true')
        observer.observe(document.body, {
          attributes: true,
          attributeFilter: ['style'],
          attributeOldValue: true
        })
      }
    }
    
    observeBody()
    // Try again after DOM is ready
    if (document.readyState !== 'complete') {
      document.addEventListener('DOMContentLoaded', observeBody)
    }
    
    return () => {
      timeouts.forEach(clearTimeout)
      observer.disconnect()
    }
  }, [])
  
  return null
}