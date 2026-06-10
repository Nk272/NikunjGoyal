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
            <body>{children}</body>
        </html>
    );
}
