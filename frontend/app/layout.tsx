import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Sidebar from './components/Sidebar'
import ChatButton from './components/ChatButton'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Fulcrum - Team Directory',
  description: 'Browse our team members and their expertise',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full bg-white">
      <body className={`${inter.className} h-full`}>
        <Sidebar />
        {children}
        <ChatButton />
      </body>
    </html>
  )
} 