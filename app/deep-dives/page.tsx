// ABOUTME: Deep Dives page for technical writeups
// ABOUTME: Placeholder structure for blog-style content

import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Deep Dives | Nikunj Goyal",
    description: "Technical writeups on performance bottlenecks, concurrency pitfalls, ML infrastructure, and systems design.",
};

interface DeepDive {
    title: string;
    category: string;
    description: string;
    comingSoon?: boolean;
}

const DEEP_DIVES: DeepDive[] = [
    {
        title: "Performance Bottlenecks in Multi-Agent Systems",
        category: "ML Systems",
        description: "Identifying and resolving latency issues when orchestrating hundreds of tools in real-time production environments.",
        comingSoon: true,
    },
    {
        title: "GPU Memory Optimization Patterns",
        category: "Performance",
        description: "Practical strategies for reducing memory footprint in CUDA applications without sacrificing parallelization.",
        comingSoon: true,
    },
    {
        title: "Concurrency Pitfalls in Python ML Pipelines",
        category: "Python",
        description: "Common threading and async mistakes in ML inference pipelines and how to avoid them.",
        comingSoon: true,
    },
    {
        title: "Trade-offs in RAG System Design",
        category: "RAG",
        description: "Chunking strategies, retrieval depth, and latency considerations when building production retrieval systems.",
        comingSoon: true,
    },
];

export default function DeepDivesPage() {
    return (
        <div className="container fade-in">
            <section className="py-16 md:py-24">
                <h1
                    className="text-3xl font-semibold tracking-tight mb-4 gradient-text"
                >
                    Deep Dives
                </h1>
                <p
                    className="text-lg mb-12"
                    style={{ color: "var(--text-secondary)" }}
                >
                    Technical writeups explaining concepts to fellow engineers. No fluff, just what you need to know.
                </p>

                <div className="space-y-4">
                    {DEEP_DIVES.map((dive, index) => (
                        <article
                            key={index}
                            className="glass-card p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
                        >
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                    <h2
                                        className="text-lg font-medium"
                                        style={{ color: "var(--text-primary)" }}
                                    >
                                        {dive.title}
                                    </h2>
                                    {dive.comingSoon && (
                                        <span
                                            className="mono text-xs px-2 py-0.5 rounded"
                                            style={{
                                                background: "var(--bg-tertiary)",
                                                color: "var(--text-muted)",
                                            }}
                                        >
                                            Coming Soon
                                        </span>
                                    )}
                                </div>
                                <p
                                    className="text-sm"
                                    style={{ color: "var(--text-secondary)" }}
                                >
                                    {dive.description}
                                </p>
                            </div>
                            <span
                                className="mono text-sm px-2 py-1 rounded shrink-0"
                                style={{
                                    background: "var(--accent-muted)",
                                    color: "var(--accent)",
                                }}
                            >
                                {dive.category}
                            </span>
                        </article>
                    ))}
                </div>
            </section>
        </div>
    );
}
