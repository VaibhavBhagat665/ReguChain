import { Inter, Outfit } from 'next/font/google'
import './globals.css'
import Providers from './providers'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const outfit = Outfit({ subsets: ['latin'], variable: '--font-outfit' })

export const metadata = {
  title: 'ReguChain Watch - Real-time Regulatory Compliance',
  description: 'AI-powered regulatory compliance monitoring with real-time RAG',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${outfit.variable} font-sans bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
