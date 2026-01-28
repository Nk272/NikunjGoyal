// ABOUTME: Experience page with role cards showing problem/solution/impact
// ABOUTME: Focuses on what was broken, what was hard, what improved

import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Experience | Nikunj Goyal",
    description: "Professional experience at Adobe and research internships. Production ML systems, multi-agent orchestration, and performance optimization.",
};

interface ExperienceItem {
    title: string;
    company: string;
    location: string;
    period: string;
    problem: string;
    solution: string;
    impact: string[];
}

const EXPERIENCES: ExperienceItem[] = [
    {
        title: "Member of Technical Staff 2",
        company: "Adobe",
        location: "Noida, India",
        period: "Jan 2025 - Present",
        problem: "Adobe Illustrator needed intelligent coordination across 100+ tools with real-time performance requirements.",
        solution: "Designed and deployed a real-time multi-agent orchestration system with aggressive caching and CDN-backed delivery for diffusion models.",
        impact: [
            "30% improvement in production workflow success rates",
            "Response times reduced to <10s for diffusion model integration",
            "90% reduction in background artifacts via vectorization pipeline overhaul",
        ],
    },
    {
        title: "Member of Technical Staff 1",
        company: "Adobe",
        location: "Noida, India",
        period: "Jul 2023 - Jan 2025",
        problem: "Object merging algorithms lacked accuracy and couldn't meet latency constraints. Edit detection in large DOMs was a bottleneck.",
        solution: "Built a high-performance object-merging algorithm with KD-tree partitioning for accelerated edit detection.",
        impact: [
            "95% pixel-level accuracy while meeting strict latency requirements",
            "Processing latency reduced from 45s to 30s through concurrency optimizations",
            "2x performance improvement in DOM manipulation pipelines",
        ],
    },
    {
        title: "Machine Learning Intern",
        company: "Adobe",
        location: "Bengaluru, India",
        period: "May 2022 - Jul 2022",
        problem: "Image captioning models lacked controllability over detail level and scene understanding.",
        solution: "Developed a detail-controllable captioning model using BERT and scene graph conditioning with abstract scene graph architectures.",
        impact: [
            ">90% caption fidelity across 10k+ images",
            "Deployed as interactive web service with real-time query modes",
        ],
    },
    {
        title: "Research Intern",
        company: "Indian Institute of Technology, Kanpur",
        location: "Kanpur, India",
        period: "Summer 2021",
        problem: "Neural machine translation for Indic languages had poor performance due to morphological complexity.",
        solution: "Implemented Seq2Seq model with copying mechanism to handle out-of-vocabulary words and rare morphological forms.",
        impact: [
            "20% BLEU score improvement across 5+ language pairs",
        ],
    },
];

export default function ExperiencePage() {
    return (
        <div className="container fade-in">
            <section className="py-16 md:py-24">
                <h1
                    className="text-3xl font-semibold tracking-tight mb-4"
                    style={{ color: "var(--text-primary)" }}
                >
                    Experience
                </h1>
                <p
                    className="text-lg mb-12"
                    style={{ color: "var(--text-secondary)" }}
                >
                    Building production ML systems and performance-critical pipelines.
                </p>

                <div className="space-y-12">
                    {EXPERIENCES.map((exp, index) => (
                        <article
                            key={index}
                            className="p-6 rounded-lg"
                            style={{
                                background: "var(--bg-secondary)",
                                border: "1px solid var(--border)",
                            }}
                        >
                            <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-4">
                                <div>
                                    <h2
                                        className="text-xl font-medium"
                                        style={{ color: "var(--text-primary)" }}
                                    >
                                        {exp.title}
                                    </h2>
                                    <p style={{ color: "var(--text-secondary)" }}>
                                        {exp.company} - {exp.location}
                                    </p>
                                </div>
                                <p
                                    className="mono text-sm mt-1 md:mt-0"
                                    style={{ color: "var(--text-muted)" }}
                                >
                                    {exp.period}
                                </p>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <h3
                                        className="text-sm font-medium uppercase tracking-wider mb-2"
                                        style={{ color: "var(--text-muted)" }}
                                    >
                                        Problem
                                    </h3>
                                    <p style={{ color: "var(--text-secondary)" }}>
                                        {exp.problem}
                                    </p>
                                </div>

                                <div>
                                    <h3
                                        className="text-sm font-medium uppercase tracking-wider mb-2"
                                        style={{ color: "var(--text-muted)" }}
                                    >
                                        Solution
                                    </h3>
                                    <p style={{ color: "var(--text-secondary)" }}>
                                        {exp.solution}
                                    </p>
                                </div>

                                <div>
                                    <h3
                                        className="text-sm font-medium uppercase tracking-wider mb-2"
                                        style={{ color: "var(--text-muted)" }}
                                    >
                                        Impact
                                    </h3>
                                    <ul className="space-y-1">
                                        {exp.impact.map((item, i) => (
                                            <li
                                                key={i}
                                                className="flex items-start gap-2"
                                                style={{ color: "var(--text-secondary)" }}
                                            >
                                                <span style={{ color: "var(--accent)" }}>-</span>
                                                {item}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        </article>
                    ))}
                </div>
            </section>
        </div>
    );
}
