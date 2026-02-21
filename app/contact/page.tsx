// ABOUTME: Contact page with collaboration opportunities
// ABOUTME: Clear CTAs for research, ML systems, and vector graphics work

import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Contact | Nikunj Goyal",
    description: "Get in touch for research collaboration, ML systems work, or vector graphics projects.",
};

const INTERESTS = [
    {
        title: "Research Collaboration",
        description: "Interested in topics at the intersection of ML systems, performance optimization, and vector graphics.",
    },
    {
        title: "ML Infrastructure",
        description: "Building scalable inference pipelines, multi-agent systems, and GPU-accelerated workflows.",
    },
    {
        title: "Vector Graphics & Explainable AI",
        description: "Algorithmic approaches to design tools and making AI systems interpretable.",
    },
];

const LINKS = [
    { label: "Email", href: "mailto:nkgoyal272@gmail.com", value: "nkgoyal272@gmail.com" },
    { label: "GitHub", href: "https://github.com/Nk272", value: "github.com/Nk272" },
    { label: "LinkedIn", href: "https://linkedin.com/in/nikunj-goyal-1831b517a", value: "linkedin.com/in/nikunj-goyal" },
];

export default function ContactPage() {
    return (
        <div className="container fade-in">
            <section className="py-16 md:py-24">
                <h1
                    className="text-3xl font-semibold tracking-tight mb-4 gradient-text"
                >
                    Contact
                </h1>
                <p
                    className="text-lg mb-12"
                    style={{ color: "var(--text-secondary)" }}
                >
                    Open to interesting conversations and collaboration opportunities.
                </p>

                <div className="grid md:grid-cols-3 gap-6 mb-16">
                    {INTERESTS.map((interest, index) => (
                        <div
                            key={index}
                            className="glass-card p-6"
                        >
                            <h2
                                className="font-medium mb-2"
                                style={{ color: "var(--text-primary)" }}
                            >
                                {interest.title}
                            </h2>
                            <p
                                className="text-sm"
                                style={{ color: "var(--text-secondary)" }}
                            >
                                {interest.description}
                            </p>
                        </div>
                    ))}
                </div>

                <div
                    className="pt-12"
                    style={{ borderTop: "1px solid var(--glass-border)" }}
                >
                    <h2
                        className="text-sm font-medium uppercase tracking-wider mb-6"
                        style={{ color: "var(--accent)" }}
                    >
                        Get in Touch
                    </h2>
                    <div className="space-y-4">
                        {LINKS.map((link, index) => (
                            <div key={index} className="flex items-center gap-4">
                                <span
                                    className="mono text-sm w-20"
                                    style={{ color: "var(--text-muted)" }}
                                >
                                    {link.label}
                                </span>
                                <a
                                    href={link.href}
                                    target={link.href.startsWith("mailto") ? undefined : "_blank"}
                                    rel={link.href.startsWith("mailto") ? undefined : "noopener noreferrer"}
                                    className="mono text-sm"
                                    style={{ color: "var(--accent)" }}
                                >
                                    {link.value}
                                </a>
                            </div>
                        ))}
                    </div>
                </div>
            </section>
        </div>
    );
}
