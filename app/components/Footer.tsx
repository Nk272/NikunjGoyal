// ABOUTME: Footer component with social links and copyright
// ABOUTME: Minimal footer matching the dark design system

const SOCIAL_LINKS = [
    { href: "https://github.com/Nk272", label: "GitHub" },
    { href: "https://linkedin.com/in/nikunj-goyal-1831b517a", label: "LinkedIn" },
    { href: "mailto:nkgoyal272@gmail.com", label: "Email" },
];

export default function Footer() {
    const currentYear = new Date().getFullYear();

    return (
        <footer
            className="py-8"
            style={{ borderTop: "1px solid var(--glass-border)" }}
        >
            <div className="container flex flex-col md:flex-row items-center justify-between gap-4">
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                    {currentYear} Nikunj Goyal
                </p>
                <div className="flex items-center gap-6">
                    {SOCIAL_LINKS.map((link) => (
                        <a
                            key={link.href}
                            href={link.href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm"
                            style={{ color: "var(--text-secondary)" }}
                        >
                            {link.label}
                        </a>
                    ))}
                </div>
            </div>
        </footer>
    );
}
