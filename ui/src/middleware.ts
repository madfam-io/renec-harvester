import createMiddleware from 'next-intl/middleware'
import { locales, defaultLocale } from './lib/i18n'

export default createMiddleware({
  locales,
  defaultLocale,
  // Don't redirect if the locale is the default one
  localePrefix: 'as-needed'
})

export const config = {
  // Match only internationalized pathnames
  matcher: ['/', '/(es|en)/:path*']
}