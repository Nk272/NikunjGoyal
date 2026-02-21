// ABOUTME: Vertical timeline component for the home page
// ABOUTME: Renders chronological career events with scroll-triggered animations

"use client";

import { useEffect, useRef } from "react";

interface TimelineEntry {
    year: string;
    side: "left" | "right";
    tag: string;
    title: string;
    subtitle: string;
    description: string;
}

const TIMELINE_DATA: TimelineEntry[] = [
    {
        year: "2025",
        side: "left",
        tag: "Role",
        title: "Member of Technical Staff 2",
        subtitle: "Adobe, Noida",
        description:
            "Multi-agent orchestration for Illustrator. 30% improvement in workflow success rates, <10s diffusion model response times.",
    },
    {
        year: "2025",
        side: "right",
        tag: "Talk",
        title: "AI Infrastructure on Kubernetes",
        subtitle: "KubeCon + CloudNativeCon, Atlanta",
        description:
            "Patterns for scalable AI infrastructure, from model serving to multi-tenant GPU clusters.",
    },
    {
        year: "2024",
        side: "left",
        tag: "Talk",
        title: "GPUs in Kubernetes",
        subtitle: "KubeCon + CloudNativeCon, Salt Lake City",
        description:
            "GPU scheduling, resource management, and best practices for GPU workloads on Kubernetes.",
    },
    {
        year: "2023",
        side: "right",
        tag: "Role",
        title: "Member of Technical Staff 1",
        subtitle: "Adobe, Noida",
        description:
            "Object-merging algorithms with KD-tree partitioning. 95% pixel-level accuracy, 2x DOM pipeline performance.",
    },
    {
        year: "2023",
        side: "left",
        tag: "Project",
        title: "Vectorization Pipeline",
        subtitle: "Graphics / ML",
        description:
            "90% reduction in background artifacts through edge refinement and adaptive quality thresholds.",
    },
    {
        year: "2022",
        side: "right",
        tag: "Internship",
        title: "Machine Learning Intern",
        subtitle: "Adobe, Bengaluru",
        description:
            "Detail-controllable image captioning using BERT and scene graph conditioning. >90% caption fidelity on 10k+ images.",
    },
    {
        year: "2022",
        side: "left",
        tag: "Project",
        title: "RAG Assistant for Arduino",
        subtitle: "RAG Systems",
        description:
            "Pinecone vector DB with embedding-based retrieval for contextual embedded systems code assistance.",
    },
    {
        year: "2021",
        side: "right",
        tag: "Internship",
        title: "Research Intern",
        subtitle: "IIT Kanpur",
        description:
            "Seq2Seq with copying mechanism for Indic language translation. 20% BLEU score improvement across 5+ language pairs.",
    },
    {
        year: "2021",
        side: "left",
        tag: "Project",
        title: "Conway's Reverse Game of Life",
        subtitle: "Algorithms / GPU",
        description:
            "GPU-optimized genetic algorithm with CUDA. 90% memory footprint reduction vs naive implementations.",
    },
    {
        year: "2019",
        side: "right",
        tag: "Education",
        title: "IIT Roorkee",
        subtitle: "Applied Mathematics",
        description:
            "Integrated M.Sc. in Applied Mathematics with focus on computational methods and optimization.",
    },
];

function GroupByYear(entries: TimelineEntry[]): { year: string; items: TimelineEntry[] }[] {
    const groups: { year: string; items: TimelineEntry[] }[] = [];
    let currentYear = "";

    for (const entry of entries) {
        if (entry.year !== currentYear) {
            currentYear = entry.year;
            groups.push({ year: currentYear, items: [] });
        }
        groups[groups.length - 1].items.push(entry);
    }

    return groups;
}

export default function Timeline() {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("visible");
                    }
                }
            },
            { threshold: 0.15, rootMargin: "0px 0px -50px 0px" }
        );

        const items = containerRef.current?.querySelectorAll(".timeline-item");
        items?.forEach((item) => observer.observe(item));

        return () => observer.disconnect();
    }, []);

    const groups = GroupByYear(TIMELINE_DATA);

    return (
        <div className="timeline" ref={containerRef}>
            <div className="timeline-line" />
            {groups.map((group) => (
                <div key={group.year}>
                    <div className="timeline-year">
                        <span>{group.year}</span>
                    </div>
                    {group.items.map((item, idx) => (
                        <div
                            key={`${group.year}-${idx}`}
                            className={`timeline-item timeline-item--${item.side}`}
                        >
                            <div className="timeline-dot" />
                            <div className="timeline-card glass-card">
                                <span className="card-tag">{item.tag}</span>
                                <h3>{item.title}</h3>
                                <p className="card-subtitle">{item.subtitle}</p>
                                <p>{item.description}</p>
                            </div>
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
}
