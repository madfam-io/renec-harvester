'use client'

import { useEffect, useState } from 'react'

interface NoSSRProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

export default function NoSSR({ children, fallback = null }: NoSSRProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    
    // Clean up browser extension injected styles
    const cleanupStyles = () => {
      const elements = document.querySelectorAll('[style*="--vsc-"]')
      elements.forEach(el => {
        if (el instanceof HTMLElement) {
          const style = el.getAttribute('style') || ''
          const cleanedStyle = style.replace(/--vsc-[^;]+;?/g, '').trim()
          if (cleanedStyle) {
            el.setAttribute('style', cleanedStyle)
          } else {
            el.removeAttribute('style')
          }
        }
      })
    }

    // Initial cleanup
    cleanupStyles()

    // Watch for changes
    const observer = new MutationObserver(() => {
      cleanupStyles()
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['style'],
      subtree: true
    })

    return () => observer.disconnect()
  }, [])

  if (!mounted) {
    return <>{fallback}</>
  }

  return <>{children}</>
}