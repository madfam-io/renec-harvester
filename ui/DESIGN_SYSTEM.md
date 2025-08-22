# RENEC Harvester UI Design System

## 🎯 Design Principles

1. **Consistency First**: Every component follows the same patterns
2. **Spanish-First**: Default language is Spanish, English as secondary
3. **Theme-Aware**: All components respect the tri-mode theme system
4. **Accessible**: WCAG AA compliant, keyboard navigable
5. **Progressive**: Start simple, reveal complexity as needed

## 🏗️ Architecture Overview

```
ui/
├── src/
│   ├── app/                    # Next.js app directory
│   │   ├── [locale]/          # Internationalized routes
│   │   │   ├── layout.tsx     # Root layout with providers
│   │   │   ├── page.tsx       # Home page
│   │   │   ├── dashboard/     # Dashboard feature
│   │   │   ├── harvest/       # Harvester feature
│   │   │   ├── data/          # Data explorer feature
│   │   │   └── settings/      # Settings feature
│   │   ├── api/               # API routes
│   │   └── globals.css        # Global styles
│   │
│   ├── components/            # Shared components
│   │   ├── ui/               # Base UI components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── modal.tsx
│   │   │   ├── tooltip.tsx
│   │   │   └── ...
│   │   ├── layout/           # Layout components
│   │   │   ├── header.tsx
│   │   │   ├── sidebar.tsx
│   │   │   ├── footer.tsx
│   │   │   └── nav.tsx
│   │   ├── features/         # Feature-specific components
│   │   │   ├── harvest/
│   │   │   ├── data/
│   │   │   └── dashboard/
│   │   └── shared/           # Shared feature components
│   │       ├── language-switcher.tsx
│   │       ├── theme-switcher.tsx
│   │       └── help-tooltip.tsx
│   │
│   ├── lib/                  # Utilities and helpers
│   │   ├── i18n/            # Internationalization
│   │   │   ├── config.ts
│   │   │   ├── provider.tsx
│   │   │   └── use-translations.ts
│   │   ├── theme/           # Theme system
│   │   │   ├── provider.tsx
│   │   │   └── use-theme.ts
│   │   ├── api/             # API client
│   │   ├── utils/           # General utilities
│   │   └── hooks/           # Custom React hooks
│   │
│   ├── styles/              # Styling system
│   │   ├── themes/
│   │   │   ├── base.css     # Base variables
│   │   │   ├── light.css    # Light theme
│   │   │   └── dark.css     # Dark theme
│   │   └── components/      # Component-specific styles
│   │
│   └── types/               # TypeScript types
│       ├── i18n.d.ts
│       ├── theme.d.ts
│       └── api.d.ts
│
├── public/
│   ├── locales/            # Translation files
│   │   ├── es/             # Spanish translations
│   │   │   ├── common.json
│   │   │   ├── harvest.json
│   │   │   ├── data.json
│   │   │   └── ...
│   │   └── en/             # English translations
│   │       └── ... (same structure)
│   └── assets/             # Static assets
│
└── tests/                  # Test files
    ├── components/
    ├── integration/
    └── e2e/
```

## 🎨 Component Architecture

### Base Component Pattern

Every component should follow this pattern:

```tsx
// components/ui/button.tsx
import { forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { useTranslations } from '@/lib/i18n'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const t = useTranslations()
    
    return (
      <button
        ref={ref}
        className={cn(
          'button-base',
          `button-${variant}`,
          `button-${size}`,
          isLoading && 'button-loading',
          disabled && 'button-disabled',
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <LoadingSpinner size={size} />
            <span>{t('common.loading')}</span>
          </>
        ) : children}
      </button>
    )
  }
)

Button.displayName = 'Button'
```

### Theme-Aware Styling

All components use CSS variables that automatically adjust:

```css
/* Base button styles */
.button-base {
  font-family: inherit;
  border-radius: var(--radius-md);
  font-weight: 500;
  transition: all var(--transition-base);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
}

/* Variant styles using theme variables */
.button-primary {
  background-color: var(--color-primary);
  color: var(--color-primary-text);
  border: 1px solid var(--color-primary);
}

.button-primary:hover:not(:disabled) {
  background-color: var(--color-primary-hover);
}

/* Size variants */
.button-sm {
  height: 32px;
  padding: 0 var(--spacing-md);
  font-size: var(--text-sm);
}

.button-md {
  height: 40px;
  padding: 0 var(--spacing-lg);
  font-size: var(--text-base);
}

.button-lg {
  height: 48px;
  padding: 0 var(--spacing-xl);
  font-size: var(--text-lg);
}
```

## 🌐 Internationalization System

### Configuration

```ts
// lib/i18n/config.ts
export const locales = ['es', 'en'] as const
export const defaultLocale = 'es'

export const messages = {
  es: {
    common: () => import('/public/locales/es/common.json'),
    harvest: () => import('/public/locales/es/harvest.json'),
    data: () => import('/public/locales/es/data.json'),
    // ... other namespaces
  },
  en: {
    common: () => import('/public/locales/en/common.json'),
    harvest: () => import('/public/locales/en/harvest.json'),
    data: () => import('/public/locales/en/data.json'),
    // ... other namespaces
  }
}
```

### Usage Pattern

```tsx
// In any component
import { useTranslations } from '@/lib/i18n'

export function MyComponent() {
  const t = useTranslations()
  
  return (
    <div>
      <h1>{t('harvest.title')}</h1>
      <p>{t('harvest.description')}</p>
      <Button>{t('common.actions.start')}</Button>
    </div>
  )
}
```

## 🎨 Theme System

### Theme Provider Setup

```tsx
// lib/theme/provider.tsx
'use client'

import { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark' | 'system'

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  resolvedTheme: 'light' | 'dark'
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('system')
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    // Load saved theme
    const saved = localStorage.getItem('theme') as Theme | null
    if (saved) setTheme(saved)
  }, [])

  useEffect(() => {
    const root = document.documentElement
    
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const updateTheme = () => {
        const systemTheme = mediaQuery.matches ? 'dark' : 'light'
        root.setAttribute('data-theme', systemTheme)
        setResolvedTheme(systemTheme)
      }
      
      updateTheme()
      mediaQuery.addEventListener('change', updateTheme)
      return () => mediaQuery.removeEventListener('change', updateTheme)
    } else {
      root.setAttribute('data-theme', theme)
      setResolvedTheme(theme)
    }
    
    localStorage.setItem('theme', theme)
  }, [theme])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within ThemeProvider')
  return context
}
```

## 📦 Core Components Library

### 1. Button
```tsx
<Button variant="primary" size="md">
  {t('common.actions.start')}
</Button>
```

### 2. Card
```tsx
<Card>
  <CardHeader>
    <CardTitle>{t('data.stats.title')}</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
</Card>
```

### 3. Input
```tsx
<Input
  label={t('common.search')}
  placeholder={t('data.search.placeholder')}
  error={errors.search}
/>
```

### 4. Select
```tsx
<Select
  label={t('harvest.config.mode.label')}
  options={[
    { value: 'crawl', label: t('harvest.config.mode.crawl') },
    { value: 'harvest', label: t('harvest.config.mode.harvest') }
  ]}
  value={mode}
  onChange={setMode}
/>
```

### 5. Modal
```tsx
<Modal
  isOpen={showConfirm}
  onClose={() => setShowConfirm(false)}
  title={t('common.confirm')}
>
  <p>{t('harvest.messages.startConfirm')}</p>
  <ModalActions>
    <Button variant="secondary" onClick={() => setShowConfirm(false)}>
      {t('common.actions.cancel')}
    </Button>
    <Button variant="primary" onClick={handleStart}>
      {t('common.actions.confirm')}
    </Button>
  </ModalActions>
</Modal>
```

## 🔧 Implementation Checklist

### Phase 1: Foundation (Current)
- [ ] Clean up existing component structure
- [ ] Implement base UI components with theme support
- [ ] Set up proper i18n configuration with next-intl
- [ ] Create consistent layout components
- [ ] Establish TypeScript types for everything

### Phase 2: Migration
- [ ] Migrate existing components to new structure
- [ ] Add full Spanish/English translations
- [ ] Ensure all text uses translation keys
- [ ] Apply theme variables everywhere
- [ ] Remove all hardcoded colors/text

### Phase 3: Enhancement
- [ ] Add loading states to all components
- [ ] Implement error boundaries
- [ ] Add keyboard navigation
- [ ] Create help tooltips system
- [ ] Build onboarding flow

### Phase 4: Testing
- [ ] Unit tests for all components
- [ ] Theme switching tests
- [ ] Language switching tests
- [ ] Accessibility tests
- [ ] E2E user flow tests

## 🚀 Best Practices

1. **No Hardcoded Text**: Every visible string must use translations
2. **No Hardcoded Colors**: Always use CSS variables
3. **Component Composition**: Build complex components from simple ones
4. **Accessibility First**: aria-labels, keyboard nav, focus management
5. **Performance**: Lazy load heavy components, memoize expensive operations
6. **Type Safety**: Full TypeScript coverage, no `any` types
7. **Error Handling**: Every component handles loading/error states

## 📊 Quality Metrics

- 100% translation coverage (no hardcoded text)
- 100% theme variable usage (no hardcoded colors)
- 100% TypeScript coverage (no implicit any)
- WCAG AA compliance on all components
- <200ms theme switch time
- <100ms language switch time
- 0 console errors/warnings

---

This design system ensures consistency, maintainability, and full coverage of bilingual and theme features.