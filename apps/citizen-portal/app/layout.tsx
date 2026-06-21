import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SARATHI Citizen Portal',
  description: 'Citizen web portal for the SARATHI digital government platform.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
