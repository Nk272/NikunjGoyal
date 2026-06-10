"use client";
// ABOUTME: Single-page portfolio with interactive bezier hero and scroll-reveal sections
// ABOUTME: Covers journey timeline, craft showcase, off-the-clock interests, and contact

import { useEffect } from "react";

export default function Home() {
    useEffect(() => {
        const nav = document.getElementById("nav");
        const handleScroll = () => {
            nav?.classList.toggle("scrolled", window.scrollY > 30);
        };
        window.addEventListener("scroll", handleScroll);

        const io = new IntersectionObserver(
            (entries) => {
                entries.forEach((e) => {
                    if (e.isIntersecting) {
                        e.target.classList.add("in");
                        io.unobserve(e.target);
                    }
                });
            },
            { threshold: 0.18 }
        );
        document
            .querySelectorAll(".reveal,.ms")
            .forEach((el) => io.observe(el));

        const svg = document.getElementById("bez");
        const P0 = { x: 70, y: 330 };
        const P3 = { x: 530, y: 90 };
        const C1 = { x: 200, y: 330 };
        const C2 = { x: 400, y: 90 };
        const base1 = { x: 200, y: 330 };
        const base2 = { x: 400, y: 90 };
        const curveEl = document.getElementById("curve");
        const h1Line = document.getElementById("h1");
        const h2Line = document.getElementById("h2");
        const p0El = document.getElementById("p0");
        const p3El = document.getElementById("p3");
        const c1El = document.getElementById("c1");
        const c2El = document.getElementById("c2");

        function SetPt(el: Element | null, p: { x: number; y: number }) {
            el?.setAttribute("cx", String(p.x));
            el?.setAttribute("cy", String(p.y));
        }
        function SetLine(
            el: Element | null,
            a: { x: number; y: number },
            b: { x: number; y: number }
        ) {
            el?.setAttribute("x1", String(a.x));
            el?.setAttribute("y1", String(a.y));
            el?.setAttribute("x2", String(b.x));
            el?.setAttribute("y2", String(b.y));
        }
        function Render() {
            curveEl?.setAttribute(
                "d",
                "M" + P0.x + " " + P0.y + " C " + C1.x + " " + C1.y +
                ", " + C2.x + " " + C2.y + ", " + P3.x + " " + P3.y
            );
            SetPt(p0El, P0);
            SetPt(p3El, P3);
            SetPt(c1El, C1);
            SetPt(c2El, C2);
            SetLine(h1Line, P0, C1);
            SetLine(h2Line, P3, C2);
        }

        let t = 0;
        let dragging: { x: number; y: number } | null = null;
        let idle = true;
        let animFrameId: number;

        function Loop() {
            if (idle) {
                t += 0.012;
                C1.x = base1.x + Math.sin(t) * 46;
                C1.y = base1.y + Math.cos(t * 0.8) * 30;
                C2.x = base2.x + Math.cos(t * 1.1) * 46;
                C2.y = base2.y + Math.sin(t) * 30;
                Render();
            }
            animFrameId = requestAnimationFrame(Loop);
        }

        function StartDrag(
            el: Element | null,
            pt: { x: number; y: number }
        ) {
            if (!el) return;
            el.addEventListener("pointerdown", (e) => {
                e.preventDefault();
                idle = false;
                dragging = pt;
                (el as HTMLElement).style.cursor = "grabbing";
                try {
                    (el as Element).setPointerCapture(
                        (e as PointerEvent).pointerId
                    );
                } catch (_) {
                    /* ignore */
                }
                const hint = document.getElementById("hint");
                if (hint) hint.style.opacity = "0";
            });
            el.addEventListener("pointerup", () => {
                dragging = null;
                (el as HTMLElement).style.cursor = "grab";
            });
        }

        StartDrag(c1El, C1);
        StartDrag(c2El, C2);

        const handlePointerMove = (e: Event) => {
            if (!dragging || !svg) return;
            const pe = e as PointerEvent;
            const r = svg.getBoundingClientRect();
            const x = ((pe.clientX - r.left) / r.width) * 600;
            const y = ((pe.clientY - r.top) / r.height) * 410;
            dragging.x = Math.max(8, Math.min(592, x));
            dragging.y = Math.max(8, Math.min(402, y));
            Render();
            const readout = document.getElementById("readout");
            if (readout) {
                readout.innerHTML =
                    "C\u2081(" + Math.round(C1.x) + ", " + Math.round(C1.y) +
                    ")<br>C\u2082(" + Math.round(C2.x) + ", " +
                    Math.round(C2.y) + ")";
            }
        };
        svg?.addEventListener("pointermove", handlePointerMove);

        Render();
        animFrameId = requestAnimationFrame(Loop);

        const jsvg = document.getElementById("jsvg");
        const jpath = document.getElementById("jpath");
        const journeyStage = document.querySelector(".journey-stage");

        function BuildJourney() {
            if (!journeyStage || !jsvg || !jpath) return;
            const nodes = Array.from(
                document.querySelectorAll(".ms .node")
            );
            if (nodes.length < 2) return;
            const sb = journeyStage.getBoundingClientRect();
            jsvg.setAttribute(
                "viewBox",
                "0 0 " + sb.width + " " + sb.height
            );
            const pts = nodes.map((n) => {
                const r = n.getBoundingClientRect();
                return {
                    x: r.left - sb.left + r.width / 2,
                    y: r.top - sb.top + r.height / 2,
                };
            });
            let d = "M" + pts[0].x + " " + pts[0].y;
            for (let i = 0; i < pts.length - 1; i++) {
                const pt0 = pts[i ? i - 1 : 0];
                const pt1 = pts[i];
                const pt2 = pts[i + 1];
                const pt3 = pts[i + 2] || pt2;
                const c1x = pt1.x + (pt2.x - pt0.x) / 6;
                const c1y = pt1.y + (pt2.y - pt0.y) / 6;
                const c2x = pt2.x - (pt3.x - pt1.x) / 6;
                const c2y = pt2.y - (pt3.y - pt1.y) / 6;
                d +=
                    " C " + c1x + " " + c1y + ", " + c2x + " " + c2y +
                    ", " + pt2.x + " " + pt2.y;
            }
            jpath.setAttribute("d", d);
            const pathEl = jpath as unknown as SVGPathElement;
            const len = pathEl.getTotalLength();
            jpath.style.strokeDasharray = String(len);
            jpath.style.strokeDashoffset = String(len);
            jpath.style.transition = "none";
            requestAnimationFrame(() => {
                jpath.style.transition = "stroke-dashoffset 2.2s ease";
                jpath.style.strokeDashoffset = "0";
            });
        }

        let resizeTimeout: ReturnType<typeof setTimeout>;
        const debounced = () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(BuildJourney, 180);
        };
        const journeyTimeout = setTimeout(BuildJourney, 400);
        window.addEventListener("resize", debounced);
        if (document.fonts?.ready) {
            document.fonts.ready.then(() =>
                setTimeout(BuildJourney, 200)
            );
        }

        return () => {
            window.removeEventListener("scroll", handleScroll);
            io.disconnect();
            cancelAnimationFrame(animFrameId);
            svg?.removeEventListener("pointermove", handlePointerMove);
            window.removeEventListener("resize", debounced);
            clearTimeout(journeyTimeout);
            clearTimeout(resizeTimeout);
        };
    }, []);

    return (
        <>
            <svg className="grain">
                <filter id="n">
                    <feTurbulence
                        type="fractalNoise"
                        baseFrequency="0.9"
                        numOctaves="3"
                    />
                </filter>
                <rect width="100%" height="100%" filter="url(#n)" />
            </svg>

            <nav id="nav">
                <div className="brand">
                    <b>{"\u25CF"}</b> Nikunj{"\u00a0"}Goyal
                    <span style={{ color: "var(--faint)" }}>
                        / portfolio
                    </span>
                </div>
                <div className="links">
                    <a href="#journey">Journey</a>
                    <a href="#craft">Craft</a>
                    <a href="#offclock">Off-Clock</a>
                    <a href="#contact">Contact</a>
                </div>
            </nav>

            <header>
                <div className="wrap">
                    <div className="hero-grid">
                        <div>
                            <div className="hero-meta">
                                <span className="chip">
                                    <b>{"\u25F7"}</b> 24{" "}
                                    <i>{"\u2197"} 25 this Oct</i>
                                </span>
                                <span className="chip">
                                    {"\u25C9"} India {"\u00b7"} 28.97{"\u00b0"}N, 77.65{"\u00b0"}E
                                </span>
                                <span className="chip">
                                    applied{"\u00a0"}maths {"\u00d7"} design
                                </span>
                            </div>
                            <h1>
                                I draw my life as a{" "}
                                <em className="curve-word">
                                    b{"\u00e9"}zier{"\u00a0"}curve
                                </em>{" "}
                                {"\u2014"} anchored in maths, smoothed by the
                                road.
                            </h1>
                            <p className="lede">
                                Five years deep in{" "}
                                <b>
                                    applied mathematics at IIT Roorkee
                                </b>
                                , three more bending pixels and curves on
                                the <b>Adobe Illustrator</b> team. I like
                                problems that live where the equation meets
                                the thing people actually touch.
                            </p>
                            <div className="hero-cta">
                                <a
                                    className="btn primary"
                                    href="#journey"
                                >
                                    Trace the journey {"\u2198"}
                                </a>
                                <a
                                    className="btn ghost"
                                    href="#contact"
                                >
                                    Get in touch
                                </a>
                            </div>
                        </div>

                        <div className="stage" id="stage">
                            <div className="hud">
                                CANVAS {"\u00b7"} 600{"\u00d7"}410 px{" "}
                                {"\u00b7"} 100%
                            </div>
                            <div className="hud2" id="readout">
                                P(t) = (1-t){"\u00b3"}P{"\u2080"} +
                                3(1-t){"\u00b2"}tP{"\u2081"}
                                <br />+ 3(1-t)t{"\u00b2"}P{"\u2082"} + t
                                {"\u00b3"}P{"\u2083"}
                            </div>
                            <div className="hint" id="hint">
                                {"\u2927"} drag the cyan handles
                            </div>
                            <svg
                                viewBox="0 0 600 410"
                                id="bez"
                                preserveAspectRatio="xMidYMid meet"
                            >
                                <path
                                    id="curve"
                                    fill="none"
                                    stroke="var(--accent)"
                                    strokeWidth="2.5"
                                />
                                <line
                                    id="h1"
                                    stroke="var(--handle)"
                                    strokeWidth="1"
                                    strokeDasharray="4 4"
                                    opacity=".7"
                                />
                                <line
                                    id="h2"
                                    stroke="var(--handle)"
                                    strokeWidth="1"
                                    strokeDasharray="4 4"
                                    opacity=".7"
                                />
                                <circle
                                    id="p0"
                                    r="6"
                                    fill="var(--accent)"
                                />
                                <circle
                                    id="p3"
                                    r="6"
                                    fill="var(--accent)"
                                />
                                <circle
                                    id="c1"
                                    r="7"
                                    fill="var(--ink)"
                                    stroke="var(--handle)"
                                    strokeWidth="2"
                                    style={{ cursor: "grab" }}
                                />
                                <circle
                                    id="c2"
                                    r="7"
                                    fill="var(--ink)"
                                    stroke="var(--handle)"
                                    strokeWidth="2"
                                    style={{ cursor: "grab" }}
                                />
                            </svg>
                        </div>
                    </div>
                </div>
            </header>

            <section id="journey">
                <div className="wrap">
                    <div className="sec-head reveal">
                        <span className="num">01</span>
                        <h2>The control points</h2>
                        <span className="sub">
                            8 years {"\u00b7"} 3 cities {"\u00b7"} 1
                            continuous curve
                        </span>
                    </div>

                    <div className="journey-stage">
                        <svg
                            className="journey-svg"
                            id="jsvg"
                            preserveAspectRatio="none"
                        >
                            <path
                                id="jpath"
                                fill="none"
                                stroke="url(#jgrad)"
                                strokeWidth="2"
                            />
                            <defs>
                                <linearGradient
                                    id="jgrad"
                                    x1="0"
                                    y1="0"
                                    x2="0"
                                    y2="1"
                                >
                                    <stop
                                        offset="0"
                                        stopColor="var(--handle)"
                                    />
                                    <stop
                                        offset="1"
                                        stopColor="var(--accent)"
                                    />
                                </linearGradient>
                            </defs>
                        </svg>

                        <div className="milestones">
                            <div className="ms">
                                <div className="card">
                                    <span className="yr">
                                        {"\u2248"} 2019 {"\u2014"} 2024{" "}
                                        {"\u00b7"} P{"\u2080"}
                                    </span>
                                    <h3>IIT Roorkee</h3>
                                    <div className="where">
                                        Master in Applied Mathematics{" "}
                                        {"\u00b7"} 5 years
                                    </div>
                                    <p>
                                        Where the foundations were laid
                                        {"\u00a0"}{"\u2014"} five years of
                                        proofs, models, and the language of
                                        curves. Also found time off the
                                        chalkboard with the campus
                                        Economics Club, arguing markets and
                                        incentives.
                                    </p>
                                    <div className="pills">
                                        <span className="pill">
                                            applied maths
                                        </span>
                                        <span className="pill">
                                            economics club
                                        </span>
                                        <span className="pill">
                                            5-yr integrated
                                        </span>
                                    </div>
                                </div>
                                <div className="node"></div>
                            </div>

                            <div className="ms">
                                <div className="node"></div>
                                <div className="card">
                                    <span className="yr">
                                        {"\u2248"} 2024 {"\u2014"} 2027{" "}
                                        {"\u00b7"} P{"\u2081"}
                                    </span>
                                    <h3>
                                        Adobe {"\u2014"} Illustrator team
                                    </h3>
                                    <div className="where">
                                        Image processing {"\u00b7"} B
                                        {"\u00e9"}zier geometry {"\u00b7"}{" "}
                                        C++ {"\u00b7"} 3 years
                                    </div>
                                    <p>
                                        Turned theory into tools millions
                                        of designers touch daily. Worked
                                        deep in image processing and the
                                        math of b{"\u00e9"}zier curves,
                                        written in performance-critical
                                        C++. Filed{" "}
                                        <b
                                            style={{
                                                color: "var(--accent)",
                                            }}
                                        >
                                            5 patents
                                        </b>{" "}
                                        along the way.
                                    </p>
                                    <div className="pills">
                                        <span className="pill hot">
                                            5 patents
                                        </span>
                                        <span className="pill">C++</span>
                                        <span className="pill">
                                            b{"\u00e9"}zier curves
                                        </span>
                                        <span className="pill">
                                            image processing
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div className="ms">
                                <div className="card">
                                    <span className="yr">
                                        2024 {"\u00b7"} P{"\u2082"}
                                    </span>
                                    <h3>
                                        KubeCon {"\u2014"} Salt Lake City
                                    </h3>
                                    <div className="where">
                                        Speaker {"\u00b7"} SLC 2024
                                    </div>
                                    <p>
                                        First time on the big stage,
                                        sharing the work with the global
                                        cloud-native community.
                                    </p>
                                    <div className="pills">
                                        <span className="pill">
                                            speaker
                                        </span>
                                        <span className="pill">
                                            talk #1
                                        </span>
                                    </div>
                                </div>
                                <div className="node"></div>
                            </div>

                            <div className="ms">
                                <div className="node"></div>
                                <div className="card">
                                    <span className="yr">
                                        2025 {"\u00b7"} P{"\u2083"}
                                    </span>
                                    <h3>
                                        KubeCon {"\u2014"} Atlanta
                                    </h3>
                                    <div className="where">
                                        Speaker {"\u00b7"} Atlanta 2025
                                    </div>
                                    <p>
                                        Back on stage a second time{" "}
                                        {"\u2014"} because once you{"'"}ve
                                        found the curve, you keep drawing
                                        it.
                                    </p>
                                    <div className="pills">
                                        <span className="pill">
                                            speaker
                                        </span>
                                        <span className="pill">
                                            talk #2
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section style={{ paddingTop: "30px" }}>
                <div className="wrap reveal">
                    <div className="band">
                        <div className="cell">
                            <div className="n">5</div>
                            <div className="l">Patents filed</div>
                        </div>
                        <div className="cell">
                            <div className="n">
                                2<span className="u">{"\u00d7"}</span>
                            </div>
                            <div className="l">KubeCon talks</div>
                        </div>
                        <div className="cell">
                            <div className="n">
                                8<span className="u">yrs</span>
                            </div>
                            <div className="l">Maths + craft</div>
                        </div>
                        <div className="cell">
                            <div className="n">
                                350<span className="u">cc</span>
                            </div>
                            <div className="l">On two wheels</div>
                        </div>
                    </div>
                </div>
            </section>

            <section id="craft">
                <div className="wrap">
                    <div className="sec-head reveal">
                        <span className="num">02</span>
                        <h2>What I actually build</h2>
                        <span className="sub">
                            the math under the pixels
                        </span>
                    </div>
                    <div className="work-grid">
                        <div className="wcard reveal">
                            <div className="ix">/ 01</div>
                            <h4>
                                B{"\u00e9"}zier & vector geometry
                            </h4>
                            <p>
                                The curves that make up every vector
                                graphic {"\u2014"} modelled, simplified,
                                and rendered so they feel effortless to the
                                person dragging a handle.
                            </p>
                            <svg
                                className="curve-bg"
                                viewBox="0 0 100 100"
                            >
                                <path
                                    d="M5 90 C 20 10, 80 10, 95 90"
                                    fill="none"
                                    stroke="var(--accent)"
                                    strokeWidth="3"
                                />
                                <circle
                                    cx="5"
                                    cy="90"
                                    r="5"
                                    fill="var(--accent)"
                                />
                                <circle
                                    cx="95"
                                    cy="90"
                                    r="5"
                                    fill="var(--accent)"
                                />
                            </svg>
                        </div>
                        <div className="wcard reveal">
                            <div className="ix">/ 02</div>
                            <h4>Image processing</h4>
                            <p>
                                Pixels as data. Filters, transforms, and
                                the numerical methods that keep images
                                sharp and fast at scale.
                            </p>
                            <svg
                                className="curve-bg"
                                viewBox="0 0 100 100"
                            >
                                <g fill="var(--handle)">
                                    <rect
                                        x="10"
                                        y="10"
                                        width="22"
                                        height="22"
                                    />
                                    <rect
                                        x="40"
                                        y="40"
                                        width="22"
                                        height="22"
                                    />
                                    <rect
                                        x="68"
                                        y="14"
                                        width="18"
                                        height="18"
                                    />
                                    <rect
                                        x="14"
                                        y="66"
                                        width="18"
                                        height="18"
                                    />
                                </g>
                            </svg>
                        </div>
                        <div className="wcard reveal">
                            <div className="ix">/ 03</div>
                            <h4>Performance C++</h4>
                            <p>
                                Where elegant math meets the metal. Tight,
                                fast, production code that ships inside
                                Illustrator.
                            </p>
                            <svg
                                className="curve-bg"
                                viewBox="0 0 100 100"
                            >
                                <text
                                    x="8"
                                    y="60"
                                    fontFamily="monospace"
                                    fontSize="34"
                                    fill="var(--lime)"
                                >
                                    {"{ }"}
                                </text>
                            </svg>
                        </div>
                        <div className="wcard reveal">
                            <div className="ix">/ 04</div>
                            <h4>Applied mathematics</h4>
                            <p>
                                The throughline. From IIT Roorkee onward{" "}
                                {"\u2014"} turning abstract structure into
                                things that solve real problems.
                            </p>
                            <svg
                                className="curve-bg"
                                viewBox="0 0 100 100"
                            >
                                <path
                                    d="M10 50 Q 30 5 50 50 T 90 50"
                                    fill="none"
                                    stroke="var(--accent)"
                                    strokeWidth="3"
                                />
                            </svg>
                        </div>
                        <div className="wcard reveal">
                            <div className="ix">/ 05</div>
                            <h4>5 patents</h4>
                            <p>
                                Ideas worth protecting {"\u2014"} novel
                                methods born at the intersection of
                                geometry, imaging, and tooling.
                            </p>
                            <svg
                                className="curve-bg"
                                viewBox="0 0 100 100"
                            >
                                <path
                                    d="M50 8 l12 26 28 3 -21 19 6 28 -25 -14 -25 14 6 -28 -21 -19 28 -3z"
                                    fill="var(--accent)"
                                />
                            </svg>
                        </div>
                        <div className="wcard reveal">
                            <div className="ix">/ 06</div>
                            <h4>Telling the story</h4>
                            <p>
                                Two KubeCon talks. Translating dense
                                technical work into something a room full
                                of engineers leans into.
                            </p>
                            <svg
                                className="curve-bg"
                                viewBox="0 0 100 100"
                            >
                                <path
                                    d="M20 70 L20 30 L50 50 L20 70z"
                                    fill="var(--handle)"
                                />
                                <path
                                    d="M55 38 a 22 22 0 0 1 0 26"
                                    fill="none"
                                    stroke="var(--handle)"
                                    strokeWidth="4"
                                />
                            </svg>
                        </div>
                    </div>
                </div>
            </section>

            <section id="offclock">
                <div className="wrap">
                    <div className="sec-head reveal">
                        <span className="num">03</span>
                        <h2>Off the clock</h2>
                        <span className="sub">the analog curve</span>
                    </div>
                    <div className="analog">
                        <div className="feature reveal">
                            <div>
                                <div className="rev">
                                    the daily commute & everything after
                                </div>
                                <h3>
                                    Royal Enfield
                                    <br />
                                    Hunter 350
                                </h3>
                                <p>
                                    Some curves you compute. This one you
                                    lean into. The bike that turns a map
                                    into a memory.
                                </p>
                            </div>
                            <div className="odo">
                                {"\u2014"} 350cc {"\u00b7"} thumping
                                single {"\u00b7"} open road {"\u2197"}
                            </div>
                            <svg
                                className="moto"
                                viewBox="0 0 200 120"
                            >
                                <g
                                    fill="none"
                                    stroke="var(--accent)"
                                    strokeWidth="4"
                                    strokeLinecap="round"
                                >
                                    <circle cx="42" cy="86" r="22" />
                                    <circle cx="158" cy="86" r="22" />
                                    <path d="M42 86 L78 86 L96 58 L140 58 L158 86" />
                                    <path d="M78 86 L70 58 L100 58" />
                                    <path d="M120 58 L132 40 L150 40" />
                                </g>
                            </svg>
                        </div>
                        <div className="advl">
                            <div className="adv reveal">
                                <div className="ic">
                                    {"\u25b2"} TREKS
                                </div>
                                <div className="big">4</div>
                                <div className="cap">
                                    mountains met on foot
                                </div>
                            </div>
                            <div className="adv reveal">
                                <div className="ic">
                                    {"\u2248"} RIVER
                                </div>
                                <div className="big">1</div>
                                <div className="cap">
                                    rafting run, fully soaked
                                </div>
                            </div>
                            <div className="adv reveal">
                                <div className="ic">
                                    {"\u2605"} PARKS
                                </div>
                                <div className="big">Disney</div>
                                <div className="cap">
                                    the happiest detour
                                </div>
                            </div>
                            <div className="adv reveal">
                                <div className="ic">
                                    {"\u2211"} CLUB
                                </div>
                                <div className="big">Econ</div>
                                <div className="cap">
                                    college economics club
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section id="contact">
                <div className="wrap reveal">
                    <div className="export">
                        <div className="bar">
                            <span
                                className="d"
                                style={{
                                    background: "var(--accent)",
                                }}
                            ></span>
                            <span
                                className="d"
                                style={{
                                    background: "var(--lime)",
                                }}
                            ></span>
                            <span
                                className="d"
                                style={{
                                    background: "var(--handle)",
                                }}
                            ></span>
                            {"\u00a0"}export {"\u00b7"}{" "}
                            lets-connect.svg
                        </div>
                        <div className="body">
                            <div>
                                <h2>
                                    Let{"'"}s draw the{" "}
                                    <em>next</em> control point
                                    together.
                                </h2>
                                <p>
                                    Open to good problems, interesting
                                    people, and the occasional ride.
                                </p>
                            </div>
                            <div className="ports">
                                <a href="mailto:nkgoyal272@gmail.com">
                                    email{" "}
                                    <span className="ar">
                                        {"\u2197"}
                                    </span>
                                </a>
                                <a
                                    href="https://linkedin.com/in/nikunj-goyal-1831b517a"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    linkedin{" "}
                                    <span className="ar">
                                        {"\u2197"}
                                    </span>
                                </a>
                                <a
                                    href="https://github.com/Nk272"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    github{" "}
                                    <span className="ar">
                                        {"\u2197"}
                                    </span>
                                </a>
                                <a href="#">
                                    resume.pdf{" "}
                                    <span className="ar">
                                        {"\u2198"}
                                    </span>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                <footer>
                    <div className="sig">
                        {"\u2014"} anchored, not fixed.
                    </div>
                    <div className="fine">
                        Nikunj Goyal {"\u00b7"} built 2026 {"\u00b7"}{" "}
                        India
                    </div>
                </footer>
            </section>
        </>
    );
}
