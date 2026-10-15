import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'UrbanSync AI | Autonomous Civic Command',
  description: 'Autonomous Municipal Synchronization & Real-Time Incident Orchestration',
  applicationName: 'UrbanSync AI',
  keywords: ['Smart City', 'Municipal Cockpit', 'Autonomous Dispatch', 'Civic Safety', 'CVRP Fleet Optimization'],
  authors: [{ name: 'UrbanSync AI Command' }],
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#0b1329',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className="font-sans min-h-screen bg-[#0b1329] text-slate-100 antialiased selection:bg-cyan-500/25 selection:text-cyan-300"
      >
        {children}
      </body>
    </html>
  );
}
