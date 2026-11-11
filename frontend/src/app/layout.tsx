import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ColdChain Sentinel | Logistics Command Center',
  description: 'Evidence-verified pharmaceutical acceptance, real-time temperature tracking, and automated payment assurance.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-canvas-950 text-slate-100 antialiased selection:bg-cyan-500/20 selection:text-cyan-300">
        {children}
      </body>
    </html>
  );
}
