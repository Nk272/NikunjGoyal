// ABOUTME: Projects page showcasing 4 deep technical projects
// ABOUTME: Each project has problem, approach, trade-offs, and impact

import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Projects | Nikunj Goyal",
    description: "Selected technical projects in ML systems, RAG pipelines, GPU optimization, and genetic algorithms.",
};

interface Project {
    title: string;
    category: string;
    problem: string;
    approach: string;
    tradeoffs: string;
    impact: string;
    future?: string;
}

const PROJECTS: Project[] = [
    {
        title: "Multi-Agent Orchestration System",
        category: "ML Systems",
        problem: "Adobe Illustrator needed intelligent coordination across 100+ tools with sub-second response times and high reliability.",
        approach: "Built a real-time orchestration layer with tool registry, health-check polling, automated regression evaluation, and aggressive caching strategies.",
        tradeoffs: "Optimized for latency over exhaustive tool search. Prioritized frequently-used tools and implemented fallback chains for reliability.",
        impact: "30% improvement in task execution success rates. Powers production workflows for Illustrator users.",
    },
    {
        title: "RAG-powered AI Assistant for Arduino",
        category: "RAG Systems",
        problem: "Embedded systems developers need contextual assistance for Arduino code, but generic LLMs lack domain-specific knowledge.",
        approach: "Integrated Pinecone vector database with embedding-based retrieval. Built a retrieval pipeline that provides contextual fixes and explanations for embedded systems code.",
        tradeoffs: "Balanced retrieval depth against response latency. Chunking strategy optimized for code semantics over arbitrary token limits.",
        impact: "Provides accurate, context-aware assistance for Arduino development with grounded responses.",
        future: "Extend to support multiple embedded platforms and real-time compilation feedback.",
    },
    {
        title: "Genetic Algorithm for Conway's Reverse Game of Life",
        category: "Algorithms / GPU",
        problem: "Finding predecessor states in cellular automata is computationally expensive with exponential search space.",
        approach: "Designed a GPU-optimized genetic algorithm leveraging CUDA for parallel fitness evaluation and population evolution.",
        tradeoffs: "Memory footprint vs. population size for parallelization. Tuned mutation rates for exploration-exploitation balance.",
        impact: "90% reduction in memory footprint compared to naive implementations while maintaining solution quality.",
    },
    {
        title: "Vectorization Pipeline Overhaul",
        category: "Graphics / ML",
        problem: "Background removal produced unusable artifacts that broke downstream vector editing workflows.",
        approach: "Complete pipeline redesign focusing on edge refinement, artifact detection, and quality metrics for automated validation.",
        tradeoffs: "Processing time vs. artifact quality. Implemented adaptive thresholds based on content complexity.",
        impact: "90% reduction in background artifacts. Enabled reliable downstream editing for production workflows.",
    },
];

export default function ProjectsPage() {
    return (
        <div className="container fade-in">
            <section className="py-16 md:py-24">
                <h1
                    className="text-3xl font-semibold tracking-tight mb-4 gradient-text"
                >
                    Selected Projects
                </h1>
                <p
                    className="text-lg mb-12"
                    style={{ color: "var(--text-secondary)" }}
                >
                    Deep dives into systems I've built. Each project represents real problems with measurable outcomes.
                </p>

                <div className="space-y-8">
                    {PROJECTS.map((project, index) => (
                        <article
                            key={index}
                            className="glass-card p-6"
                        >
                            <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-4">
                                <h2
                                    className="text-xl font-medium"
                                    style={{ color: "var(--text-primary)" }}
                                >
                                    {project.title}
                                </h2>
                                <span
                                    className="mono text-sm px-2 py-1 rounded mt-2 md:mt-0"
                                    style={{
                                        background: "var(--accent-muted)",
                                        color: "var(--accent)",
                                    }}
                                >
                                    {project.category}
                                </span>
                            </div>

                            <div className="grid md:grid-cols-2 gap-6">
                                <div>
                                    <h3
                                        className="text-sm font-medium uppercase tracking-wider mb-2"
                                        style={{ color: "var(--accent)" }}
                                    >
                                        Problem
                                    </h3>
                                    <p
                                        className="text-sm leading-relaxed"
                                        style={{ color: "var(--text-secondary)" }}
                                    >
                                        {project.problem}
                                    </p>
                                </div>

                                <div>
                                    <h3
                                        className="text-sm font-medium uppercase tracking-wider mb-2"
                                        style={{ color: "var(--accent)" }}
                                    >
                                        Approach
                                    </h3>
                                    <p
                                        className="text-sm leading-relaxed"
                                        style={{ color: "var(--text-secondary)" }}
                                    >
                                        {project.approach}
                                    </p>
                                </div>

                                <div>
                                    <h3
                                        className="text-sm font-medium uppercase tracking-wider mb-2"
                                        style={{ color: "var(--accent)" }}
                                    >
                                        Trade-offs
                                    </h3>
                                    <p
                                        className="text-sm leading-relaxed"
                                        style={{ color: "var(--text-secondary)" }}
                                    >
                                        {project.tradeoffs}
                                    </p>
                                </div>

                                <div>
                                    <h3
                                        className="text-sm font-medium uppercase tracking-wider mb-2"
                                        style={{ color: "var(--accent)" }}
                                    >
                                        Impact
                                    </h3>
                                    <p
                                        className="text-sm leading-relaxed"
                                        style={{ color: "var(--text-secondary)" }}
                                    >
                                        {project.impact}
                                    </p>
                                </div>

                                {project.future && (
                                    <div className="md:col-span-2">
                                        <h3
                                            className="text-sm font-medium uppercase tracking-wider mb-2"
                                            style={{ color: "var(--accent)" }}
                                        >
                                            What I'd Improve
                                        </h3>
                                        <p
                                            className="text-sm leading-relaxed"
                                            style={{ color: "var(--text-secondary)" }}
                                        >
                                            {project.future}
                                        </p>
                                    </div>
                                )}
                            </div>
                        </article>
                    ))}
                </div>
            </section>
        </div>
    );
}
