'use client'

import { useEffect } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Aggressive cleanup of browser extension injections
    const cleanup = () => {
      // Remove VS Code extension styles
      const html = document.documentElement
      const body = document.body
      
      // Clean HTML element
      if (html.hasAttribute('style')) {
        const style = html.getAttribute('style') || ''
        if (style.includes('--vsc-')) {
          html.removeAttribute('style')
        }
      }
      
      // Clean body element  
      if (body.hasAttribute('style')) {
        const style = body.getAttribute('style') || ''
        if (style.includes('--vsc-')) {
          body.removeAttribute('style')
        }
      }
      
      // Remove any CSS custom properties
      const computedStyle = getComputedStyle(html)
      for (const prop of Array.from(computedStyle)) {
        if (prop.startsWith('--vsc-')) {
          html.style.removeProperty(prop)
        }
      }
    }
    
    // Run cleanup immediately
    cleanup()
    
    // Run cleanup on next tick
    setTimeout(cleanup, 0)
    
    // Set up mutation observer
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
          cleanup()
        }
      })
    })
    
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['style']
    })
    
    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ['style']
    })
    
    return () => observer.disconnect()
  }, [])
  
  return <>{children}</>
}