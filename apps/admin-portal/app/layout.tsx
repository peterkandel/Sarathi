import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SARATHI Admin Portal',
  description: 'Government administrative portal for the SARATHI platform.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
