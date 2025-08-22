# UI Implementation Plan - Clean Architecture

## 🚨 Current Issues

1. **Inconsistent Structure**
   - Mixed approaches (some components client-side, some not)
   - No clear separation between UI components and features
   - Translations in wrong location (should be in public/)
   - Theme files scattered

2. **Incomplete Coverage**
   - Language switcher doesn't actually work
   - Only partial English translations
   - Many components still use hardcoded text
   - Theme variables not applied consistently

3. **Missing Core Setup**
   - No proper next-intl configuration
   - No routing for language switching
   - No base component library
   - No consistent styling approach

## 🎯 Implementation Strategy

### Step 1: Clean Foundation (Day 1)

**1.1 Restructure Directories**
```bash
# Move translations to public
mkdir -p public/locales/{es,en}
mv ui/locales/es-MX/* public/locales/es/
mv ui/locales/en-US/* public/locales/en/

# Create proper component structure  
mkdir -p src/components/{ui,layout,features,shared}
mkdir -p src/lib/{i18n,theme,utils,hooks}
mkdir -p src/types
```

**1.2 Configure next-intl**
```ts
// next.config.js
const withNextIntl = require('next-intl/plugin')('./src/lib/i18n.ts')

module.exports = withNextIntl({
  // existing config
})
```

**1.3 Set up i18n routing**
```ts
// middleware.ts
import createMiddleware from 'next-intl/middleware'

export default createMiddleware({
  locales: ['es', 'en'],
  defaultLocale: 'es'
})

export const config = {
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)']
}
```

### Step 2: Base Components (Day 2)

**2.1 Create UI Component Library**
- Button (all variants, sizes, states)
- Input (with label, error, help text)
- Select (native and custom)
- Card (header, content, footer)
- Modal (portal-based)
- Tooltip (accessible)
- Badge (status indicators)
- Spinner (loading states)

**2.2 Styling System**
```css
/* components/ui/styles.module.css */
.button {
  /* Use CSS modules with theme variables */
  composes: button-base from global;
  background: var(--color-primary);
  color: var(--color-primary-text);
}
```

### Step 3: Layout Components (Day 2)

**3.1 Main Layout Structure**
- RootLayout (with all providers)
- Header (logo, nav, theme/lang switchers)
- Sidebar (collapsible navigation)
- MainContent (with breadcrumbs)
- Footer (minimal info)

**3.2 Navigation System**
```tsx
const navigation = {
  main: [
    { name: t('nav.dashboard'), href: '/dashboard', icon: LayoutDashboard },
    { name: t('nav.harvest'), href: '/harvest', icon: Database },
    { name: t('nav.data'), href: '/data', icon: Search },
    { name: t('nav.settings'), href: '/settings', icon: Settings }
  ]
}
```

### Step 4: Feature Migration (Day 3)

**4.1 Harvest Feature**
- Move ScrapingControls → features/harvest/
- Create HarvestConfig component
- Create HarvestStatus component
- Create HarvestResults component
- Full Spanish/English translations

**4.2 Data Explorer Feature**
- Move DataExplorer → features/data/
- Create DataTable component
- Create DataFilters component
- Create DataExport component
- Full translations

**4.3 Dashboard Feature**
- Move MonitoringDashboard → features/dashboard/
- Create StatsCards component
- Create ActivityFeed component
- Create QuickActions component
- Full translations

### Step 5: Integration (Day 4)

**5.1 Wire Everything Together**
- Update all imports
- Apply theme classes everywhere
- Replace all hardcoded text
- Add loading/error states
- Test theme switching
- Test language switching

**5.2 Create Missing Translations**
- Complete all English translations
- Add pluralization rules
- Add date/time formatting
- Add number formatting

### Step 6: Polish & Testing (Day 5)

**6.1 Accessibility**
- Keyboard navigation
- ARIA labels
- Focus management
- Screen reader testing

**6.2 Performance**
- Code splitting
- Lazy loading
- Image optimization
- Bundle analysis

**6.3 Testing**
- Component unit tests
- Integration tests
- E2E tests
- Visual regression tests

## 📋 File-by-File Tasks

### Delete/Move:
- [x] `/ui/locales/` → `/public/locales/`
- [ ] Scattered theme files → unified system
- [ ] Mixed component approaches → consistent pattern

### Create New:
- [ ] `/src/lib/i18n.ts` - Proper i18n setup
- [ ] `/src/middleware.ts` - Language routing
- [ ] `/src/components/ui/*` - Base components
- [ ] `/src/app/[locale]/layout.tsx` - Locale-aware layout
- [ ] Complete English translations

### Refactor:
- [ ] All existing components to use translations
- [ ] All styles to use theme variables
- [ ] All layouts to new structure
- [ ] All features to new organization

## 🎯 Success Criteria

1. **100% Translation Coverage**
   - No hardcoded text anywhere
   - Full Spanish translations
   - Full English translations
   - Proper pluralization

2. **100% Theme Coverage**
   - No hardcoded colors
   - All components theme-aware
   - Smooth transitions
   - Persistent selection

3. **Consistent Architecture**
   - Clear component hierarchy
   - Predictable file locations
   - Reusable patterns
   - Type safety throughout

4. **Great UX**
   - Instant theme switching
   - Instant language switching
   - Accessible to all users
   - Beginner-friendly

## 🚀 Quick Start Commands

```bash
# 1. Install additional dependencies
npm install next-intl @formatjs/intl-localematcher negotiator
npm install --save-dev @types/negotiator

# 2. Run development server
npm run dev

# 3. Build for production
npm run build

# 4. Run tests
npm test
```

## ⚠️ Critical Path

The most important items to fix FIRST:

1. **Set up next-intl properly** - Nothing works without this
2. **Move translations to public/** - Required for next-intl
3. **Create base Button component** - Sets pattern for all others
4. **Fix language switcher** - Currently does nothing
5. **Apply theme variables** - Many components ignore theme

Once these are done, everything else follows naturally.

---

*Estimated Timeline: 5 days for complete implementation*
*Priority: High - Current UI is broken and inconsistent*