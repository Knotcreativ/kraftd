/**
 * Root Layout
 */

import type { Metadata } from 'next'
import { ReactQueryProvider } from '../components/providers/ReactQueryProvider'
import { ThemeProvider } from '../components/providers/ThemeProvider'
import AppShell from '../components/layout/AppShell'
import '@/app/globals.css'

export const metadata: Metadata = {
  title: 'KRAFTD - Document Intelligence',
  description: 'Intelligent document processing and conversion',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <ReactQueryProvider>
            <AppShell>
              {children}
            </AppShell>
          </ReactQueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
