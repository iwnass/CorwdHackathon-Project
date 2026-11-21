import { useEffect, useRef, useState } from "react";

/* ================= GradientWaves (background) ================= */
export function GradientWaves({ rows = 9, light = 0.12 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const c = canvasRef.current;
    const g = c.getContext("2d");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let W, H, raf, swell = 0, mx = -1e4, my = -1e4;

    const size = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = window.innerWidth;
      H = window.innerHeight;
      c.width = W * dpr;
      c.height = H * dpr;
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const onMove = (e) => { mx = e.clientX; my = e.clientY; };
    const onDown = () => { swell = 1; };
    size();
    window.addEventListener("resize", size);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerdown", onDown);

    const frame = (ts) => {
      const t = ts / 1000;
      swell *= 0.95;
      g.clearRect(0, 0, W, H);

      const sky = g.createLinearGradient(0, 0, 0, H);
      sky.addColorStop(0, "#120f17");
      sky.addColorStop(0.38, "#241447");
      sky.addColorStop(0.5, "#3b2a6b");
      sky.addColorStop(1, "#120f17");
      g.fillStyle = sky;
      g.fillRect(0, 0, W, H);

      const horizon = H * 0.46;
      for (let r = 0; r < rows; r++) {
        const k = r / (rows - 1);
        const y0 = horizon + Math.pow(k, 1.6) * (H - horizon) * 0.95;
        const amp = 6 + k * 46 + swell * 24;
        const freq = 0.004 - k * 0.0021;
        const spd = reduce ? 0 : 0.35 + k * 0.5;

        g.beginPath();
        g.moveTo(0, H);
        for (let x = 0; x <= W; x += 8) {
          const y =
            y0 +
            Math.sin(x * freq + t * spd + r * 1.7) * amp +
            Math.sin(x * freq * 2.3 - t * spd * 0.8 + r) * amp * 0.35;
          g.lineTo(x, y);
        }
        g.lineTo(W, H);
        g.closePath();

        const gr = g.createLinearGradient(0, y0 - amp, 0, y0 + amp * 3 + 60);
        gr.addColorStop(0, `rgba(84,199,206,${0.55 - k * 0.25})`);
        gr.addColorStop(0.35, `rgba(119,48,248,${0.55 - k * 0.1})`);
        gr.addColorStop(1, "rgba(18,15,23,.95)");
        g.fillStyle = gr;
        g.fill();
      }

      // dimmer cursor light (lower `light` prop = darker)
      const R = 220 + swell * 200;
      const lg = g.createRadialGradient(mx, my, 0, mx, my, R);
      lg.addColorStop(0, `rgba(190,240,245,${light + swell * 0.08})`);
      lg.addColorStop(1, "rgba(190,240,245,0)");
      g.globalCompositeOperation = "lighter";
      g.fillStyle = lg;
      g.fillRect(0, 0, W, H);
      g.globalCompositeOperation = "source-over";

      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", size);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerdown", onDown);
    };
  }, [rows, light]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{ position: "fixed", inset: 0, width: "100%", height: "100%", display: "block" }}
    />
  );
}

/* ================= DepthText (extruded, parallax) ================= */
const hex = (h, i) => parseInt(h.substr(i, 2), 16);
const mix = (a, b, t) =>
  `rgb(${[1, 3, 5].map((i) => Math.round(hex(a, i) + (hex(b, i) - hex(a, i)) * t)).join(",")})`;

export function DepthText({
  text = "Athens Pulse",
  faceColor = "#2ac2cc",
  depthColor = "#652ad0",
  layers = 14,
  reach = 26,
}) {
  const [p, setP] = useState({ x: 0, y: 0 });
  const target = useRef({ x: 0, y: 0 });

  useEffect(() => {
    let raf;
    const onMove = (e) => {
      target.current = {
        x: (e.clientX / window.innerWidth - 0.5) * 2,
        y: (e.clientY / window.innerHeight - 0.5) * 2,
      };
    };
    const tick = () => {
      setP((c) => ({
        x: c.x + (target.current.x - c.x) * 0.08,
        y: c.y + (target.current.y - c.y) * 0.08,
      }));
      raf = requestAnimationFrame(tick);
    };
    window.addEventListener("pointermove", onMove);
    raf = requestAnimationFrame(tick);
    return () => {
      window.removeEventListener("pointermove", onMove);
      cancelAnimationFrame(raf);
    };
  }, []);

  const stack = Array.from({ length: layers + 1 }, (_, i) => layers - i); // back to front

  return (
    <h1 className="depth-text" aria-label={text}>
      {stack.map((i) => {
        const d = i / layers;
        const isFace = i === 0;
        return (
          <span
            key={i}
            aria-hidden="true"
            className={`depth-layer${isFace ? " face" : ""}`}
            style={{
              color: isFace ? faceColor : mix(depthColor, "#1b0c3e", d),
              transform: `translate(${-p.x * d * reach}px, ${-p.y * d * reach + d * 10}px)`,
            }}
          >
            {text}
          </span>
        );
      })}
    </h1>
  );
}

/* ================= Stickers ================= */
const C = { marble: "#f4efe6", clay: "#c8643c", aegean: "#1a719f", olive: "#6b8e3a", gold: "#e2b53f", night: "#2a2140", sky: "#8fd3e0" };

const Badge = ({ fill }) => <circle cx="50" cy="50" r="47" fill={fill} />;

const ART = {
  parthenon: (
    <>
      <Badge fill={C.aegean} />
      <polygon points="14,40 50,20 86,40" fill={C.marble} />
      <rect x="16" y="42" width="68" height="5" fill={C.marble} />
      {[0, 1, 2, 3, 4, 5].map((i) => <rect key={i} x={19 + i * 11.4} y="49" width="6" height="26" fill={C.marble} />)}
      <rect x="14" y="76" width="72" height="4" fill={C.marble} />
      <rect x="10" y="81" width="80" height="4" fill={C.marble} />
    </>
  ),
  column: (
    <>
      <Badge fill={C.sky} />
      <circle cx="36" cy="30" r="7" fill={C.marble} />
      <circle cx="64" cy="30" r="7" fill={C.marble} />
      <rect x="36" y="25" width="28" height="9" fill={C.marble} />
      <rect x="40" y="34" width="20" height="46" fill={C.marble} />
      {[44, 50, 56].map((x) => <line key={x} x1={x} y1="36" x2={x} y2="78" stroke="#cfc6b4" strokeWidth="1.5" />)}
      <rect x="33" y="80" width="34" height="6" fill={C.marble} />
    </>
  ),
  owl: (
    <>
      <Badge fill={C.night} />
      <polygon points="30,26 34,14 42,24" fill="#b5763a" />
      <polygon points="70,26 66,14 58,24" fill="#b5763a" />
      <ellipse cx="50" cy="56" rx="25" ry="29" fill="#b5763a" />
      <ellipse cx="50" cy="64" rx="14" ry="18" fill="#e8c9a0" />
      <circle cx="40" cy="44" r="10" fill="#fff" />
      <circle cx="60" cy="44" r="10" fill="#fff" />
      <circle cx="40" cy="44" r="4.5" fill={C.night} />
      <circle cx="60" cy="44" r="4.5" fill={C.night} />
      <polygon points="46,50 54,50 50,58" fill={C.gold} />
    </>
  ),
  wreath: (
    <>
      <Badge fill={C.marble} />
      {[30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((a) => (
        <ellipse key={a} cx="50" cy="19" rx="5" ry="11" fill={a % 60 ? C.olive : "#5a7b2d"} transform={`rotate(${a} 50 50)`} />
      ))}
      <circle cx="50" cy="50" r="9" fill={C.gold} />
    </>
  ),
  amphora: (
    <>
      <Badge fill={C.gold} />
      <path d="M38 26 C28 26 26 40 34 46 M62 26 C72 26 74 40 66 46" stroke={C.clay} strokeWidth="4" fill="none" />
      <path d="M40 18 h20 v8 c10 4 14 14 12 28 c-2 14 -10 22 -22 24 c-12 -2 -20 -10 -22 -24 c-2 -14 2 -24 12 -28 z" fill={C.clay} />
      <rect x="30" y="46" width="40" height="6" fill={C.night} opacity=".8" />
      <rect x="40" y="78" width="20" height="6" fill={C.clay} />
    </>
  ),
  meander: (
    <>
      <Badge fill={C.clay} />
      <g stroke={C.marble} strokeWidth="5" fill="none" strokeLinejoin="miter">
        <path d="M14 66 H30 V46 H46 V60 H38 V53" />
        <path d="M54 66 H70 V46 H86 V60 H78 V53" />
        <line x1="14" y1="34" x2="86" y2="34" />
      </g>
    </>
  ),
  lycabettus: (
    <>
      <Badge fill={C.sky} />
      <path d="M6 80 Q50 8 94 80 Z" fill={C.olive} />
      <rect x="44" y="26" width="12" height="9" fill={C.marble} />
      <polygon points="42,26 50,19 58,26" fill={C.clay} />
      <path d="M6 80 H94 A47 47 0 0 1 6 80 Z" fill={C.aegean} opacity=".9" />
    </>
  ),
  tram: (
    <>
      <Badge fill={C.night} />
      <path d="M50 34 L44 22 H60" stroke={C.marble} strokeWidth="2.5" fill="none" />
      <rect x="18" y="34" width="64" height="34" rx="8" fill={C.marble} />
      {[24, 42, 60].map((x) => <rect key={x} x={x} y="40" width="14" height="12" rx="2" fill={C.aegean} />)}
      <rect x="18" y="56" width="64" height="5" fill={C.clay} />
      <circle cx="32" cy="72" r="5" fill={C.marble} />
      <circle cx="68" cy="72" r="5" fill={C.marble} />
    </>
  ),
  coffee: (
    <>
      <Badge fill={C.clay} />
      <path d="M26 44 h40 v14 a16 16 0 0 1 -16 16 h-8 a16 16 0 0 1 -16 -16 z" fill={C.marble} />
      <path d="M66 48 h4 a7 7 0 0 1 0 14 h-5" stroke={C.marble} strokeWidth="4" fill="none" />
      <rect x="28" y="46" width="36" height="5" fill={C.night} opacity=".8" />
      <path d="M40 36 c-4 -5 4 -8 0 -13 M52 36 c-4 -5 4 -8 0 -13" stroke={C.marble} strokeWidth="3" fill="none" strokeLinecap="round" />
    </>
  ),
  stadium: (
    <>
      <Badge fill={C.olive} />
      <path d="M22 78 V44 a28 28 0 0 1 56 0 V78" stroke={C.marble} strokeWidth="9" fill="none" />
      <path d="M34 78 V46 a16 16 0 0 1 32 0 V78" stroke={C.gold} strokeWidth="4" fill="none" />
      <line x1="16" y1="78" x2="84" y2="78" stroke={C.marble} strokeWidth="5" />
    </>
  ),
  helmet: (
    <>
      <Badge fill={C.aegean} />
      <path d="M32 24 C34 12 62 8 74 20" stroke={C.clay} strokeWidth="6" fill="none" strokeLinecap="round" />
      <path d="M26 64 C26 36 40 26 54 26 C70 26 76 40 74 56 L70 72 H60 L58 62 C52 64 44 64 38 68 L36 76 H28 Z" fill={C.gold} />
      <path d="M44 48 h14 v6 h-14 z" fill={C.night} />
    </>
  ),
  cat: (
    <>
      <Badge fill={C.gold} />
      <path d="M64 78 C84 78 86 56 74 52" stroke={C.night} strokeWidth="6" fill="none" strokeLinecap="round" />
      <ellipse cx="50" cy="62" rx="17" ry="21" fill={C.night} />
      <circle cx="50" cy="36" r="13" fill={C.night} />
      <polygon points="38,30 40,15 49,25" fill={C.night} />
      <polygon points="62,30 60,15 51,25" fill={C.night} />
      <circle cx="45" cy="36" r="2.6" fill={C.gold} />
      <circle cx="55" cy="36" r="2.6" fill={C.gold} />
    </>
  ),
  word: (
    <>
      <rect x="4" y="22" width="92" height="56" rx="14" fill={C.marble} />
      <rect x="9" y="27" width="82" height="46" rx="10" fill="none" stroke={C.aegean} strokeWidth="2.5" />
      <text x="50" y="58" textAnchor="middle" fontSize="23" fontWeight="800" fill={C.aegean} fontFamily="system-ui, sans-serif">ΑΘΗΝΑ</text>
    </>
  ),
};

// left/top in %, size in px, rot in degrees
const STICKERS = [
  { art: "parthenon", left: 3, top: 5, size: 160, rot: -8 },
  { art: "owl", left: 80, top: 4, size: 130, rot: 10 },
  { art: "amphora", left: 2, top: 34, size: 118, rot: 9 },
  { art: "column", left: 88, top: 31, size: 110, rot: -6 },
  { art: "lycabettus", left: 4, top: 72, size: 150, rot: 6 },
  { art: "tram", left: 72, top: 74, size: 150, rot: -7 },
  { art: "word", left: 21, top: 6, size: 140, rot: -4 },
  { art: "wreath", left: 44, top: 1, size: 112, rot: 6 },
  { art: "helmet", left: 79, top: 52, size: 120, rot: -5 },
  { art: "meander", left: 14, top: 55, size: 100, rot: -10 },
  { art: "coffee", left: 45, top: 86, size: 104, rot: 8 },
  { art: "stadium", left: 22, top: 80, size: 118, rot: -6 },
  { art: "cat", left: 89, top: 85, size: 94, rot: 7 },
];

const stickerStyle = (s, i) => ({
  left: `${s.left}%`,
  top: `${s.top}%`,
  width: `clamp(56px, ${s.size * 0.08}vw, ${s.size}px)`,
  "--r": `${s.rot}deg`,
  animationDelay: `${i * 70}ms`,
});

// Realistic stickers: drop transparent PNGs into /public/stickers, named after
// each key above (parthenon.png, owl.png, amphora.png, column.png, lycabettus.png,
// tram.png, word.png, wreath.png, helmet.png, meander.png, coffee.png,
// stadium.png, cat.png). Any file that is missing falls back to the drawn version.
function Sticker({ s, i }) {
  const [failed, setFailed] = useState(false);
  const style = stickerStyle(s, i);
  if (failed) {
    return (
      <svg className="sticker" viewBox="0 0 100 100" style={style}>
        {ART[s.art]}
      </svg>
    );
  }
  return (
    <img
      className="sticker"
      src={`/stickers/${s.art}.png`}
      alt=""
      style={style}
      onError={() => setFailed(true)}
    />
  );
}

export function StickerBomb() {
  return (
    <div className="stickers" aria-hidden="true">
      {STICKERS.map((s, i) => (
        <Sticker key={s.art} s={s} i={i} />
      ))}
    </div>
  );
}

/* ================= Parthenon behind the title ================= */
function ParthenonBackdrop() {
  return (
    <svg className="backdrop" viewBox="0 14 100 76" aria-hidden="true">
      <g fill="#f4efe6">
        <polygon points="14,40 50,20 86,40" />
        <rect x="16" y="42" width="68" height="5" />
        {[0, 1, 2, 3, 4, 5].map((i) => <rect key={i} x={19 + i * 11.4} y="49" width="6" height="26" />)}
        <rect x="14" y="76" width="72" height="4" />
        <rect x="10" y="81" width="80" height="4" />
      </g>
    </svg>
  );
}

/* ================= Home page ================= */
const LINKS = [
  { label: "Events", href: "#" },
  { label: "Transit", href: "#" },
  { label: "EV Charging", href: "#" },
];

export default function Home() {
  return (
    <>
      <style>{css}</style>
      <GradientWaves />
      <StickerBomb />
      <main className="home">
        <div className="hero">
          <ParthenonBackdrop />
          <DepthText text="Athens Pulse" faceColor="#2ac2cc" depthColor="#652ad0" />
        </div>
        <p className="tag">Athens, live: what the city is doing right now.</p>
        <nav aria-label="Project links" className="links">
          {LINKS.map((l) => (
            <a key={l.label} href={l.href}>{l.label}</a>
          ))}
        </nav>
      </main>
    </>
  );
}

const css = `
@import url("https://fonts.googleapis.com/css2?family=Unbounded:wght@800&family=Instrument+Sans:wght@400;600&display=swap");
html, body, #root { height: 100%; margin: 0; background: #120f17; }
.home {
  position: relative; z-index: 2; min-height: 100vh; box-sizing: border-box;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 2rem; padding: 2rem 1.25rem; text-align: center;
  font-family: "Instrument Sans", system-ui, sans-serif; color: #f1ecfa;
}
.hero { position: relative; width: fit-content; }
.backdrop {
  position: absolute; left: 50%; top: 50%; z-index: -1; pointer-events: none;
  width: clamp(260px, 48vw, 640px); height: auto; opacity: .3;
  transform: translate(-50%, -78%);
  filter: drop-shadow(0 0 18px rgba(143, 211, 224, .35));
}
.depth-text {
  margin: 0 auto; position: relative; width: fit-content;
  font-family: "Unbounded", system-ui, sans-serif; font-weight: 800;
  font-size: clamp(2.6rem, 11vw, 8rem); line-height: 1; letter-spacing: -0.02em;
}
.depth-layer { display: block; white-space: nowrap; will-change: transform; position: absolute; inset: 0; }
.depth-layer.face { position: relative; }
.tag { margin: 0; max-width: 34ch; font-size: 1.15rem; line-height: 1.5; color: #d6cfe6; }
.links { display: flex; flex-wrap: wrap; gap: 0.75rem; justify-content: center; }
.links a {
  color: #f1ecfa; text-decoration: none; font-weight: 600; padding: 0.8rem 1.4rem;
  border: 1.5px solid rgba(84,199,206,.6); border-radius: 999px;
  background: rgba(18,15,23,.55); backdrop-filter: blur(6px);
  transition: background .2s, border-color .2s;
}
.links a:hover { background: rgba(101,42,208,.55); border-color: #54c7ce; }
.links a:focus-visible { outline: 3px solid #54c7ce; outline-offset: 3px; }

.stickers { position: fixed; inset: 0; z-index: 1; pointer-events: none; overflow: hidden; }
.sticker {
  position: absolute; height: auto; transform: rotate(var(--r));
  filter: drop-shadow(2px 0 0 #fff) drop-shadow(-2px 0 0 #fff)
          drop-shadow(0 2px 0 #fff) drop-shadow(0 -2px 0 #fff)
          drop-shadow(0 6px 8px rgba(0,0,0,.45));
  animation: slap .45s cubic-bezier(.2,1.4,.4,1) both;
}
@keyframes slap {
  from { transform: rotate(var(--r)) scale(1.6); opacity: 0; }
  to   { transform: rotate(var(--r)) scale(1);   opacity: 1; }
}
@media (max-width: 640px) { .sticker:nth-child(n+9) { display: none; } }
@media (prefers-reduced-motion: reduce) { .sticker { animation: none; } }
`;
