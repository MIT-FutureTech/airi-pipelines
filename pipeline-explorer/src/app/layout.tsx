import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { NavHeader } from "@/shared/components/NavHeader";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AIRI Pipeline Explorer",
  description: "Interactive map of the AI Risk Initiative data pipelines",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-surface text-text-primary font-[family-name:var(--font-geist-sans)]">
        <NavHeader />
        <main className="flex-1 min-h-0">{children}</main>
      </body>
    </html>
  );
}
