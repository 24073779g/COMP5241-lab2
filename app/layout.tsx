import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Note Taking App',
  description: 'A simple note taking app with Supabase',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 min-h-screen">{children}</body>
    </html>
  )
}