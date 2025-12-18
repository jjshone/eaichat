import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
    title: 'eaichat - AI E-commerce Platform',
    description: 'Production-grade AI-powered e-commerce chat platform with vector search, multi-LLM support, and real-time recommendations.',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" className="dark">
            <body className={inter.className}>
                <div className="min-h-screen bg-background">
                    {children}
                </div>
            </body>
        </html>
    )
}
