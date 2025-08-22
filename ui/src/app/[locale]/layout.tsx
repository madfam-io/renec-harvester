import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import { ThemeProvider } from 'next-themes'
import ExtensionCleanup from '@/components/ExtensionCleanup'
import '../globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Cosechador RENEC | RENEC Harvester',
  description: 'Herramienta para extraer y analizar datos del Registro Nacional de Estándares de Competencia | Tool for extracting and analyzing data from the National Registry of Competency Standards',
  keywords: ['RENEC', 'CONOCER', 'competency standards', 'estándares de competencia', 'México'],
  authors: [{ name: 'RENEC Harvester Team' }],
  openGraph: {
    title: 'Cosechador RENEC',
    description: 'Extracción y análisis de datos del RENEC',
    type: 'website',
  },
}

interface LocaleLayoutProps {
  children: React.ReactNode
  params: { locale: string }
}

export default async function LocaleLayout({
  children,
  params: { locale }
}: LocaleLayoutProps) {
  // Load messages for the current locale
  const messages = await getMessages()

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Apply theme before first paint to prevent flash
              try {
                const theme = localStorage.getItem('theme') || 'system';
                if (theme === 'system') {
                  const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                  document.documentElement.setAttribute('data-theme', systemTheme);
                } else {
                  document.documentElement.setAttribute('data-theme', theme);
                }
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body className={inter.className} suppressHydrationWarning>
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider
            attribute="data-theme"
            defaultTheme="system"
            enableSystem={true}
            disableTransitionOnChange={false}
          >
            <ExtensionCleanup />
            {children}
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  )
}