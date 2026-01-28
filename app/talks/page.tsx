// ABOUTME: Talks page showcasing speaking engagements
// ABOUTME: KubeCon and other technical presentations

import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Talks | Nikunj Goyal",
    description: "Speaking engagements at KubeCon and technical conferences on GPUs in Kubernetes and AI infrastructure.",
};

interface Talk {
    title: string;
    venue: string;
    location: string;
    date: string;
    description: string;
}

const TALKS: Talk[] = [
    {
        title: "GPUs in Kubernetes",
        venue: "KubeCon + CloudNativeCon North America",
        location: "Salt Lake City, USA",
        date: "2024",
        description: "Deep dive into GPU scheduling, resource management, and best practices for running GPU workloads on Kubernetes clusters.",
    },
    {
        title: "AI Infrastructure on Kubernetes",
        venue: "KubeCon + CloudNativeCon North America",
        location: "Atlanta, USA",
        date: "2025",
        description: "Patterns for building scalable AI infrastructure, from model serving to multi-tenant GPU clusters.",
    },
];

export default function TalksPage() {
    return (
        <div className="container fade-in">
            <section className="py-16 md:py-24">
                <h1
                    className="text-3xl font-semibold tracking-tight mb-4"
                    style={{ color: "var(--text-primary)" }}
                >
                    Talks & Writing
                </h1>
                <p
                    className="text-lg mb-12"
                    style={{ color: "var(--text-secondary)" }}
                >
                    Speaking at conferences about GPUs, Kubernetes, and AI infrastructure.
                </p>

                <div className="space-y-6">
                    {TALKS.map((talk, index) => (
                        <article
                            key={index}
                            className="p-6 rounded-lg"
                            style={{
                                background: "var(--bg-secondary)",
                                border: "1px solid var(--border)",
                            }}
                        >
                            <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-3">
                                <h2
                                    className="text-xl font-medium"
                                    style={{ color: "var(--text-primary)" }}
                                >
                                    {talk.title}
                                </h2>
                                <span
                                    className="mono text-sm mt-1 md:mt-0"
                                    style={{ color: "var(--text-muted)" }}
                                >
                                    {talk.date}
                                </span>
                            </div>
                            <p
                                className="text-sm mb-3"
                                style={{ color: "var(--accent)" }}
                            >
                                {talk.venue} - {talk.location}
                            </p>
                            <p style={{ color: "var(--text-secondary)" }}>
                                {talk.description}
                            </p>
                        </article>
                    ))}
                </div>
            </section>
        </div>
    );
}
