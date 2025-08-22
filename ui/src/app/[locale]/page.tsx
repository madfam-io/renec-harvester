'use client'

import { useState } from 'react'
import { Settings, Database, Activity } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { Header } from '@/components/layout/header'
import { WelcomeModal } from '@/components/shared/welcome-modal'
import ScrapingControls from '@/components/ScrapingControls'
import MonitoringDashboard from '@/components/MonitoringDashboard'
import DataExplorer from '@/components/DataExplorer'

export default function Home() {
  const [activeTab, setActiveTab] = useState('controls')
  const [isScrapingActive, setIsScrapingActive] = useState(false)
  const t = useTranslations('common')

  const tabs = [
    { id: 'controls', labelKey: 'navigation.harvest', icon: Settings },
    { id: 'monitor', labelKey: 'navigation.monitor', icon: Activity },
    { id: 'data', labelKey: 'navigation.data', icon: Database },
  ]

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-background)' }}>
      {/* Welcome Modal */}
      <WelcomeModal />
      
      {/* Header with theme and language switcher */}
      <Header />

      {/* Status Bar */}
      <div style={{
        backgroundColor: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)'
      }}>
        <div className="container mx-auto px-4 py-2">
          <div className="flex items-center justify-between">
            <div style={{
              fontSize: 'var(--text-sm)',
              color: 'var(--color-text-secondary)'
            }}>
              {t('app.description')}
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-sm)',
              padding: 'var(--spacing-xs) var(--spacing-md)',
              borderRadius: 'var(--radius-full)',
              fontSize: 'var(--text-sm)',
              fontWeight: '500',
              backgroundColor: isScrapingActive ? 'var(--color-success-bg)' : 'var(--color-secondary)',
              color: isScrapingActive ? 'var(--color-success-text)' : 'var(--color-secondary-text)',
              border: isScrapingActive ? '1px solid var(--color-success-border)' : 'none'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: isScrapingActive ? 'var(--color-success)' : 'var(--color-text-tertiary)',
                animation: isScrapingActive ? 'pulse 2s infinite' : 'none'
              }} />
              {isScrapingActive ? t('status.running') : t('status.idle')}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav style={{
        backgroundColor: 'var(--color-surface-elevated)',
        borderBottom: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div className="container mx-auto px-4">
          <div className="flex gap-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--spacing-sm)',
                    padding: 'var(--spacing-lg) 0',
                    borderBottom: `2px solid ${isActive ? 'var(--color-primary)' : 'transparent'}`,
                    fontWeight: '500',
                    fontSize: 'var(--text-sm)',
                    color: isActive ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                    transition: 'color var(--transition-base)',
                    backgroundColor: 'transparent',
                    border: 'none',
                    borderBottom: `2px solid ${isActive ? 'var(--color-primary)' : 'transparent'}`,
                    cursor: 'pointer'
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.color = 'var(--color-primary)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.color = 'var(--color-text-secondary)'
                    }
                  }}
                >
                  <Icon style={{ width: '16px', height: '16px' }} />
                  <span>{t(tab.labelKey)}</span>
                </button>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div style={{
          backgroundColor: 'var(--color-surface-elevated)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-md)',
          padding: 'var(--spacing-xl)'
        }}>
          {activeTab === 'controls' && (
            <ScrapingControls 
              isActive={isScrapingActive}
              onToggle={setIsScrapingActive}
            />
          )}
          {activeTab === 'monitor' && <MonitoringDashboard />}
          {activeTab === 'data' && <DataExplorer />}
        </div>
      </main>

      {/* Footer */}
      <footer style={{
        marginTop: 'auto',
        borderTop: '1px solid var(--color-border)',
        backgroundColor: 'var(--color-surface)'
      }}>
        <div className="container mx-auto px-4 py-4">
          <div style={{
            textAlign: 'center',
            fontSize: 'var(--text-sm)',
            color: 'var(--color-text-tertiary)'
          }}>
            {t('app.name')} v0.2.0 • {new Date().getFullYear()} • 
            <a 
              href="/help" 
              style={{
                color: 'var(--color-primary)',
                textDecoration: 'none',
                marginLeft: 'var(--spacing-xs)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.textDecoration = 'underline'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.textDecoration = 'none'
              }}
            >
              {t('navigation.help')}
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}