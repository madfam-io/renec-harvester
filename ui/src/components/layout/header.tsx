'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { ThemeSwitch } from '@/lib/theme/theme-switch'
import { LanguageSwitcher } from '@/components/shared/language-switcher'

export function Header() {
  const t = useTranslations('common')

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 40,
      borderBottom: '1px solid var(--color-border)',
      backgroundColor: 'var(--color-surface-elevated)',
      boxShadow: 'var(--shadow-sm)'
    }}>
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2">
              <div style={{
                height: '32px',
                width: '32px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{
                  color: 'var(--color-primary-text)',
                  fontWeight: 'bold'
                }}>R</span>
              </div>
              <span style={{
                fontSize: 'var(--text-xl)',
                fontWeight: '600',
                color: 'var(--color-primary)'
              }}>
                {t('app.name')}
              </span>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <Link 
              href="/dashboard" 
              style={{
                color: 'var(--color-text-secondary)',
                transition: 'color var(--transition-base)',
                textDecoration: 'none'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--color-primary)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--color-text-secondary)'
              }}
            >
              {t('navigation.dashboard')}
            </Link>
            <Link 
              href="/harvest" 
              style={{
                color: 'var(--color-text-secondary)',
                transition: 'color var(--transition-base)',
                textDecoration: 'none'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--color-primary)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--color-text-secondary)'
              }}
            >
              {t('navigation.harvest')}
            </Link>
            <Link 
              href="/data" 
              style={{
                color: 'var(--color-text-secondary)',
                transition: 'color var(--transition-base)',
                textDecoration: 'none'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--color-primary)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--color-text-secondary)'
              }}
            >
              {t('navigation.data')}
            </Link>
            <Link 
              href="/help" 
              style={{
                color: 'var(--color-text-secondary)',
                transition: 'color var(--transition-base)',
                textDecoration: 'none'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--color-primary)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--color-text-secondary)'
              }}
            >
              {t('navigation.help')}
            </Link>
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <ThemeSwitch />
          </div>
        </div>
      </div>
    </header>
  )
}