// ABOUTME: Header navigation component for the portfolio
// ABOUTME: Glass-effect fixed nav with links to all main sections

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
    { href: "/", label: "Home" },
    { href: "/experience", label: "Experience" },
    { href: "/projects", label: "Projects" },
    { href: "/deep-dives", label: "Deep Dives" },
    { href: "/talks", label: "Talks" },
    { href: "/about", label: "About" },
    { href: "/contact", label: "Contact" },
];

export default function Navigation() {
    const pathname = usePathname();

    return (
        <header
            className="fixed top-0 left-0 right-0 z-50"
            style={{
                background: "rgba(5, 5, 8, 0.8)",
                backdropFilter: "blur(12px)",
                WebkitBackdropFilter: "blur(12px)",
                borderBottom: "1px solid var(--glass-border)",
            }}
        >
            <nav className="container flex items-center justify-between h-16">
                <Link
                    href="/"
                    className="font-semibold text-lg tracking-tight gradient-text"
                >
                    NK
                </Link>
                <ul className="flex items-center gap-6">
                    {NAV_ITEMS.slice(1).map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <li key={item.href}>
                                <Link
                                    href={item.href}
                                    className="text-sm transition-colors"
                                    style={{
                                        color: isActive ? "var(--accent)" : "var(--text-secondary)",
                                    }}
                                >
                                    {item.label}
                                </Link>
                            </li>
                        );
                    })}
                </ul>
            </nav>
        </header>
    );
}
