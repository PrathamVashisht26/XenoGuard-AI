import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "XenoGuard AI — Intelligent Global Transaction Validation",
  description:
    "AI-powered transaction data validation and recovery platform. Validate, explain, fix, and download cleaned international transaction datasets.",
  keywords: "CSV validation, transaction data, AI data quality, data recovery, XenoGuard",
  openGraph: {
    title: "XenoGuard AI",
    description: "Intelligent Global Transaction Validation & Recovery Platform",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
