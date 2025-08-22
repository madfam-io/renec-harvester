import type { Metadata } from 'next'
import ExtensionCleanup from '@/components/ExtensionCleanup'
import './globals.css'

export const metadata: Metadata = {
  title: 'RENEC Harvester',
  description: 'Site-wide public data harvester for México\'s RENEC platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <ExtensionCleanup />
        {children}
      </body>
    </html>
  )
}