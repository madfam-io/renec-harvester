'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useLocale, useTranslations } from 'next-intl'
import { Languages } from 'lucide-react'

export function LanguageSwitcher() {
  const locale = useLocale()
  const router = useRouter()
  const pathname = usePathname()
  const t = useTranslations('common.language')

  const switchLanguage = () => {
    const newLocale = locale === 'es' ? 'en' : 'es'
    // Remove current locale from pathname if present
    const pathWithoutLocale = pathname.replace(/^\/[a-z]{2}/, '') || '/'
    const newPath = `/${newLocale}${pathWithoutLocale}`
    router.push(newPath)
  }

  const currentLanguage = locale === 'es' ? t('spanish') : t('english')
  const switchToLanguage = locale === 'es' ? t('english') : t('spanish')

  return (
    <button
      onClick={switchLanguage}
      style={{
        padding: 'var(--spacing-sm)',
        borderRadius: 'var(--radius-md)',
        border: 'none',
        backgroundColor: 'transparent',
        color: 'var(--color-text-secondary)',
        cursor: 'pointer',
        transition: 'all var(--transition-base)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-xs)'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = 'var(--color-hover)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent'
      }}
      aria-label={`${t('switchLanguage')} (${switchToLanguage})`}
      title={`${t('switchLanguage')} - ${switchToLanguage}`}
    >
      <Languages size={20} />
      <span style={{ fontSize: 'var(--text-sm)', fontWeight: '500', textTransform: 'uppercase' }}>
        {locale}
      </span>
    </button>
  )
}