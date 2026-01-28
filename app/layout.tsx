// ABOUTME: Root layout with navigation, footer, and SEO metadata
// ABOUTME: Wraps all pages with consistent structure

import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navigation from "./components/Navigation";
import Footer from "./components/Footer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Nikunj Goyal | ML Systems & Vector Graphics Engineer",
  description: "Member of Technical Staff at Adobe. Building scalable GenAI systems, vector graphics pipelines, and production ML infrastructure.",
  keywords: ["ML Systems", "Vector Graphics", "GPU", "Kubernetes", "Adobe", "GenAI"],
  authors: [{ name: "Nikunj Goyal" }],
  openGraph: {
    title: "Nikunj Goyal | ML Systems & Vector Graphics Engineer",
    description: "Engineering intelligence into design - ML, Vector graphics, Performance",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Navigation />
        <main className="pt-16 min-h-screen">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
