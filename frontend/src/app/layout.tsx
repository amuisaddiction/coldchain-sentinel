import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ColdChain Sentinel | Pharmaceutical Evidence Verification & Payment Assurance',
  description: 'Evidence-verified shipment acceptance and PayPal payment assurance for temperature-sensitive cold chain logistics.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-obsidian-900 text-obsidian-100 antialiased selection:bg-obsidian-750 selection:text-white">
        {children}
      </body>
    </html>
  );
}
