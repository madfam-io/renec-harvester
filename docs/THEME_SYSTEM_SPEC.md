# Tri-Mode Theme System Specification

## 🎨 Overview

RENEC Harvester will implement a sophisticated theme system supporting three modes:
- **Auto**: Follows system preferences
- **Light**: Clean, professional appearance
- **Dark**: Reduced eye strain, OLED-friendly

## 🌗 Theme Modes

### Auto Mode (Default)
- Detects OS/browser preference via `prefers-color-scheme`
- Updates automatically when system changes
- Smooth transitions between themes
- No flash of incorrect theme (FOIT)

### Light Mode
- Primary mode for daytime use
- High contrast for readability
- CONOCER brand alignment
- Print-friendly colors

### Dark Mode
- Reduces blue light emission
- OLED screen optimization (true blacks)
- Maintains readability
- Preserves brand identity

## 🎨 Design Tokens

### Color Palette Structure

```css
:root {
  /* Brand Colors - Constant across themes */
  --brand-conocer: #1B4F8A;
  --brand-conocer-light: #2E6AA8;
  --brand-accent: #E35D1C;
  
  /* Semantic Colors - Theme specific */
  --color-background: var(--theme-background);
  --color-surface: var(--theme-surface);
  --color-surface-elevated: var(--theme-surface-elevated);
  
  --color-text-primary: var(--theme-text-primary);
  --color-text-secondary: var(--theme-text-secondary);
  --color-text-tertiary: var(--theme-text-tertiary);
  
  --color-border: var(--theme-border);
  --color-border-subtle: var(--theme-border-subtle);
  
  /* Functional Colors */
  --color-success: var(--theme-success);
  --color-warning: var(--theme-warning);
  --color-error: var(--theme-error);
  --color-info: var(--theme-info);
  
  /* Interactive States */
  --color-hover: var(--theme-hover);
  --color-active: var(--theme-active);
  --color-focus: var(--theme-focus);
  --color-disabled: var(--theme-disabled);
}
```

### Light Theme Values

```css
[data-theme="light"] {
  /* Backgrounds */
  --theme-background: #FFFFFF;
  --theme-surface: #F8F9FA;
  --theme-surface-elevated: #FFFFFF;
  
  /* Text */
  --theme-text-primary: #1A1A1A;
  --theme-text-secondary: #4A4A4A;
  --theme-text-tertiary: #6C6C6C;
  
  /* Borders */
  --theme-border: #E0E0E0;
  --theme-border-subtle: #F0F0F0;
  
  /* Functional */
  --theme-success: #28A745;
  --theme-warning: #FFC107;
  --theme-error: #DC3545;
  --theme-info: #17A2B8;
  
  /* Interactive */
  --theme-hover: rgba(0, 0, 0, 0.04);
  --theme-active: rgba(0, 0, 0, 0.08);
  --theme-focus: rgba(27, 79, 138, 0.2);
  --theme-disabled: rgba(0, 0, 0, 0.12);
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}
```

### Dark Theme Values

```css
[data-theme="dark"] {
  /* Backgrounds */
  --theme-background: #0A0A0A;
  --theme-surface: #1A1A1A;
  --theme-surface-elevated: #242424;
  
  /* Text */
  --theme-text-primary: #F5F5F5;
  --theme-text-secondary: #B8B8B8;
  --theme-text-tertiary: #888888;
  
  /* Borders */
  --theme-border: #333333;
  --theme-border-subtle: #222222;
  
  /* Functional */
  --theme-success: #4CAF50;
  --theme-warning: #FFB74D;
  --theme-error: #F44336;
  --theme-info: #29B6F6;
  
  /* Interactive */
  --theme-hover: rgba(255, 255, 255, 0.08);
  --theme-active: rgba(255, 255, 255, 0.12);
  --theme-focus: rgba(46, 106, 168, 0.4);
  --theme-disabled: rgba(255, 255, 255, 0.12);
  
  /* Shadows (subtle in dark mode) */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);
}
```

## 🔄 Theme Switching

### User Interface

```tsx
interface ThemeSwitcherProps {
  position: 'header' | 'settings' | 'both';
  showLabels?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

// Visual representation
[☀️ Light] [🌙 Dark] [✨ Auto]
```

### Implementation Requirements

1. **No Flash of Unstyled Content (FOUC)**
   - Theme detected and applied before first paint
   - Script in document head
   - CSS variables immediately available

2. **Smooth Transitions**
   ```css
   * {
     transition: background-color 0.3s ease,
                 color 0.3s ease,
                 border-color 0.3s ease;
   }
   ```

3. **Persistence**
   - Save preference to localStorage
   - Key: `renec-theme-preference`
   - Values: `light`, `dark`, `auto`

4. **System Integration**
   ```javascript
   // Watch for system theme changes
   window.matchMedia('(prefers-color-scheme: dark)')
     .addEventListener('change', handleSystemThemeChange);
   ```

## 🎯 Component Adaptations

### Navigation
- Light: White background with subtle shadow
- Dark: Dark surface with border

### Cards
- Light: White with gray border
- Dark: Elevated surface with subtle border

### Buttons
- Primary: Brand color (adjusted for contrast)
- Secondary: Theme-aware backgrounds
- Ghost: Transparent with theme borders

### Forms
- Light: White inputs with gray borders
- Dark: Dark inputs with lighter borders
- Focus states respect theme

### Data Tables
- Light: Alternating row colors (#FFF, #F8F9FA)
- Dark: Alternating row colors (#1A1A1A, #242424)
- Hover states theme-specific

### Charts
- Theme-aware color palettes
- Grid lines match theme
- Labels use appropriate text colors

## 📱 Responsive Considerations

### Mobile
- System theme detection works on all devices
- Theme switcher accessible in mobile menu
- Reduced motion for theme transitions on mobile

### Tablet/Desktop
- Theme switcher in header
- Keyboard shortcuts (Ctrl+Shift+T)
- Hover states for theme options

## ♿ Accessibility

### Contrast Ratios
- Normal text: 4.5:1 minimum
- Large text: 3:1 minimum
- UI components: 3:1 minimum
- Tested with both themes

### Focus Indicators
- Visible in both themes
- Consistent focus ring color
- High contrast against backgrounds

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
  }
}
```

### Screen Reader Support
- Theme names announced
- Current theme state available
- Keyboard navigable

## 🧪 Testing Strategy

### Visual Regression Tests
- Screenshot comparisons for both themes
- Component library documentation
- Automated theme switching tests

### Contrast Testing
- Automated WCAG compliance
- Manual verification of edge cases
- Real device testing

### Performance
- Theme switch timing (<50ms)
- No layout shift
- Minimal repaints

## 🚀 Implementation Guide

### 1. Theme Provider Setup
```tsx
import { ThemeProvider } from 'next-themes'

export default function App({ Component, pageProps }) {
  return (
    <ThemeProvider
      attribute="data-theme"
      defaultTheme="auto"
      enableSystem={true}
      disableTransitionOnChange={false}
    >
      <Component {...pageProps} />
    </ThemeProvider>
  )
}
```

### 2. Theme Hook Usage
```tsx
import { useTheme } from 'next-themes'

function ThemeSwitch() {
  const { theme, setTheme, systemTheme } = useTheme()
  const currentTheme = theme === 'system' ? systemTheme : theme
  
  return (
    <select value={theme} onChange={e => setTheme(e.target.value)}>
      <option value="system">Auto</option>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
    </select>
  )
}
```

### 3. CSS Variable Usage
```css
.card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  box-shadow: var(--shadow-sm);
}
```

## 📊 Theme Analytics

Track theme usage for insights:
- Most popular theme choice
- Time of day patterns
- System vs manual selection
- Theme switch frequency

## 🔮 Future Enhancements

### Phase 2
- Custom theme builder
- Preset themes (High Contrast, Colorblind)
- Theme scheduling (auto-switch by time)

### Phase 3
- User-defined color schemes
- Export/import themes
- Organization-wide theme settings

---

*Last updated: August 22, 2025*  
*Default: Auto mode*  
*Themes: Light, Dark, Auto*