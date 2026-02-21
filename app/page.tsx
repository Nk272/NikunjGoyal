// ABOUTME: Home page with bold hero section and vertical career timeline
// ABOUTME: First impression page combining experience, projects, and talks chronologically

import Timeline from "./components/Timeline";

const SOCIAL_LINKS = [
  { href: "https://github.com/Nk272", label: "GitHub" },
  { href: "https://linkedin.com/in/nikunj-goyal-1831b517a", label: "LinkedIn" },
  { href: "mailto:nkgoyal272@gmail.com", label: "Email" },
];

const FOCUS_AREAS = [
  "GenAI Systems",
  "Vector Graphics",
  "GPU Infrastructure",
  "Production ML",
];

export default function Home() {
  return (
    <div className="fade-in">
      <section
        style={{
          padding: "6rem 0 4rem",
          textAlign: "center",
          position: "relative",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "600px",
            height: "600px",
            background:
              "radial-gradient(circle, rgba(56,189,248,0.04) 0%, transparent 70%)",
            pointerEvents: "none",
          }}
        />

        <p
          className="mono"
          style={{
            fontSize: "0.85rem",
            color: "var(--text-muted)",
            marginBottom: "1rem",
            letterSpacing: "0.1em",
            textTransform: "uppercase",
          }}
        >
          Member of Technical Staff, Adobe
        </p>

        <h1
          className="gradient-text"
          style={{
            fontSize: "clamp(3rem, 8vw, 5.5rem)",
            fontWeight: 700,
            letterSpacing: "-0.03em",
            lineHeight: 1.1,
            marginBottom: "1.5rem",
          }}
        >
          Nikunj Goyal
        </h1>

        <p
          style={{
            fontSize: "1.25rem",
            color: "var(--text-secondary)",
            maxWidth: "600px",
            margin: "0 auto 2rem",
            lineHeight: 1.6,
          }}
        >
          Building production ML systems, multi-agent orchestration, and
          GPU-accelerated pipelines at Adobe.
          <br />
          <span className="mono" style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            IIT Roorkee, Applied Mathematics
          </span>
        </p>

        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "0.75rem",
            marginBottom: "3rem",
          }}
        >
          {SOCIAL_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              target={link.href.startsWith("mailto") ? undefined : "_blank"}
              rel={link.href.startsWith("mailto") ? undefined : "noopener noreferrer"}
              className="glass-card"
              style={{
                padding: "0.5rem 1.25rem",
                fontSize: "0.85rem",
                color: "var(--text-primary)",
                display: "inline-block",
              }}
            >
              {link.label}
            </a>
          ))}
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "0.75rem",
            flexWrap: "wrap",
          }}
        >
          {FOCUS_AREAS.map((area) => (
            <span
              key={area}
              className="mono"
              style={{
                fontSize: "0.75rem",
                padding: "0.3rem 0.75rem",
                borderRadius: "4px",
                background: "var(--accent-muted)",
                color: "var(--accent)",
              }}
            >
              {area}
            </span>
          ))}
        </div>
      </section>

      <section className="container" style={{ paddingBottom: "4rem" }}>
        <h2
          style={{
            textAlign: "center",
            fontSize: "0.8rem",
            letterSpacing: "0.15em",
            textTransform: "uppercase",
            color: "var(--text-muted)",
            marginBottom: "1rem",
          }}
        >
          Timeline
        </h2>
        <Timeline />
      </section>
    </div>
  );
}
