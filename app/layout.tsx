// ABOUTME: Root layout with global styles and metadata
// ABOUTME: Minimal wrapper for the single-page portfolio

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "Nikunj Goyal \u2014 Applied Maths, Curves & the Road",
    description:
        "Five years of applied mathematics at IIT Roorkee, three more bending pixels and curves on the Adobe Illustrator team.",
    keywords: [
        "Applied Mathematics",
        "Bezier Curves",
        "Vector Graphics",
        "Adobe",
        "IIT Roorkee",
    ],
    authors: [{ name: "Nikunj Goyal" }],
    openGraph: {
        title: "Nikunj Goyal \u2014 Applied Maths, Curves & the Road",
        description:
            "Applied maths, vector graphics, and the road.",
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
            <head>
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
                <link
                    href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Hanken+Grotesk:wght@300..800&family=JetBrains+Mono:wght@300..600&display=swap"
                    rel="stylesheet"
                />
            </head>
            <body>{children}</body>
        </html>
    );
}
