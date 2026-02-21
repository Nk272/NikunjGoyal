// ABOUTME: About page with engineering philosophy
// ABOUTME: Values in systems design and problem-solving approach

import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "About | Nikunj Goyal",
    description: "Engineering philosophy, approach to hard problems, and what excites me about systems design.",
};

const PHILOSOPHY = {
    approach: [
        "Start with the problem, not the solution. Understand constraints before writing code.",
        "Measure before optimizing. Intuition about bottlenecks is often wrong.",
        "Ship incrementally. Small, validated changes beat large rewrites.",
        "Read the error messages. They usually tell you exactly what's wrong.",
    ],
    values: [
        "Simplicity over cleverness. The best code is code you don't have to debug.",
        "Explicit over implicit. Magic is the enemy of maintainability.",
        "Performance matters. Latency is a feature, not an afterthought.",
        "Documentation as code. If it's not documented, it doesn't exist.",
    ],
    excites: [
        "Systems that need to be fast and correct simultaneously",
        "Multi-agent coordination and tool orchestration",
        "GPU optimization and memory-constrained computing",
        "Vector graphics algorithms and computational geometry",
        "Making ML systems reliable in production",
    ],
};

export default function AboutPage() {
    return (
        <div className="container fade-in">
            <section className="py-16 md:py-24">
                <h1
                    className="text-3xl font-semibold tracking-tight mb-4 gradient-text"
                >
                    About
                </h1>
                <p
                    className="text-lg mb-12"
                    style={{ color: "var(--text-secondary)" }}
                >
                    How I think about engineering problems.
                </p>

                <div className="space-y-8">
                    <div className="glass-card p-6">
                        <h2
                            className="text-sm font-medium uppercase tracking-wider mb-4"
                            style={{ color: "var(--accent)" }}
                        >
                            Approach to Hard Problems
                        </h2>
                        <ul className="space-y-3">
                            {PHILOSOPHY.approach.map((item, index) => (
                                <li
                                    key={index}
                                    className="flex items-start gap-3"
                                    style={{ color: "var(--text-secondary)" }}
                                >
                                    <span
                                        className="mono text-sm shrink-0"
                                        style={{ color: "var(--accent)" }}
                                    >
                                        {String(index + 1).padStart(2, "0")}
                                    </span>
                                    {item}
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className="glass-card p-6">
                        <h2
                            className="text-sm font-medium uppercase tracking-wider mb-4"
                            style={{ color: "var(--accent)" }}
                        >
                            Values in Systems Design
                        </h2>
                        <ul className="space-y-3">
                            {PHILOSOPHY.values.map((item, index) => (
                                <li
                                    key={index}
                                    className="flex items-start gap-3"
                                    style={{ color: "var(--text-secondary)" }}
                                >
                                    <span
                                        className="mono text-sm shrink-0"
                                        style={{ color: "var(--accent)" }}
                                    >
                                        {String(index + 1).padStart(2, "0")}
                                    </span>
                                    {item}
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className="glass-card p-6">
                        <h2
                            className="text-sm font-medium uppercase tracking-wider mb-4"
                            style={{ color: "var(--accent)" }}
                        >
                            What Excites Me
                        </h2>
                        <ul className="space-y-3">
                            {PHILOSOPHY.excites.map((item, index) => (
                                <li
                                    key={index}
                                    className="flex items-start gap-3"
                                    style={{ color: "var(--text-secondary)" }}
                                >
                                    <span style={{ color: "var(--accent)" }}>-</span>
                                    {item}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </section>
        </div>
    );
}
