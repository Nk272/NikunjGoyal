// ABOUTME: Home page with hero section, intro, and current focus areas
// ABOUTME: First impression targeting senior engineers and ML teams

import Link from "next/link";

const FOCUS_AREAS = [
  "GenAI Systems",
  "Vector Graphics",
  "GPU Infrastructure",
  "Production ML",
];

const SOCIAL_LINKS = [
  { href: "https://github.com/Nk272", label: "GitHub" },
  { href: "https://linkedin.com/in/nikunj-goyal-1831b517a", label: "LinkedIn" },
];

export default function Home() {
  return (
    <div className="container fade-in">
      <section className="py-24 md:py-32">
        <p
          className="mono text-sm mb-4"
          style={{ color: "var(--text-muted)" }}
        >
          Member of Technical Staff, Adobe
        </p>

        <h1
          className="text-4xl md:text-5xl font-semibold tracking-tight mb-4"
          style={{ color: "var(--text-primary)" }}
        >
          Nikunj Goyal
        </h1>

        <p
          className="text-xl md:text-2xl mb-8"
          style={{ color: "var(--text-secondary)" }}
        >
          Engineering intelligence into design{" "}
          <span className="mono" style={{ color: "var(--accent)" }}>
            {"->"}
          </span>{" "}
          ML, Vector graphics, Performance
        </p>

        <p
          className="text-lg max-w-2xl mb-8 leading-relaxed"
          style={{ color: "var(--text-secondary)" }}
        >
          I build production ML systems that ship. Currently focused on multi-agent
          orchestration, vectorization pipelines, and GPU-accelerated inference at
          Adobe. IIT Roorkee, Applied Mathematics.
        </p>

        <div className="flex items-center gap-4 mb-16">
          {SOCIAL_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 text-sm font-medium rounded-md transition-colors"
              style={{
                background: "var(--bg-secondary)",
                color: "var(--text-primary)",
                border: "1px solid var(--border)",
              }}
            >
              {link.label}
            </a>
          ))}
        </div>

        <div>
          <h2
            className="text-sm font-medium uppercase tracking-wider mb-4"
            style={{ color: "var(--text-muted)" }}
          >
            Current Focus
          </h2>
          <div className="flex flex-wrap gap-3">
            {FOCUS_AREAS.map((area) => (
              <span
                key={area}
                className="mono text-sm px-3 py-1 rounded"
                style={{
                  background: "var(--accent-muted)",
                  color: "var(--accent)",
                }}
              >
                {area}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section
        className="py-16"
        style={{ borderTop: "1px solid var(--border)" }}
      >
        <div className="grid md:grid-cols-3 gap-8">
          <Link
            href="/experience"
            className="group p-6 rounded-lg transition-colors"
            style={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border)",
            }}
          >
            <h3
              className="font-medium mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              Experience
            </h3>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Adobe, IIT Kanpur - Production ML, multi-agent systems
            </p>
          </Link>

          <Link
            href="/projects"
            className="group p-6 rounded-lg transition-colors"
            style={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border)",
            }}
          >
            <h3
              className="font-medium mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              Projects
            </h3>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              RAG systems, GPU optimization, genetic algorithms
            </p>
          </Link>

          <Link
            href="/talks"
            className="group p-6 rounded-lg transition-colors"
            style={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border)",
            }}
          >
            <h3
              className="font-medium mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              Talks
            </h3>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              KubeCon - GPUs in Kubernetes, AI infrastructure
            </p>
          </Link>
        </div>
      </section>
    </div>
  );
}
