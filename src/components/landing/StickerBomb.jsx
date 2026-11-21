/* Athens sticker bomb (landing page). Artwork from your design, unchanged. */
import { useState } from 'react'

const C = { marble: '#f4efe6', clay: '#c8643c', aegean: '#1a719f', olive: '#6b8e3a', gold: '#e2b53f', night: '#2a2140', sky: '#8fd3e0' };

const Badge = ({ fill }) => <circle cx='50' cy='50' r='47' fill={fill} />;

const ART = {
  parthenon: (
    <>
      <Badge fill={C.aegean} />
      <polygon points='14,40 50,20 86,40' fill={C.marble} />
      <rect x='16' y='42' width='68' height='5' fill={C.marble} />
      {[0, 1, 2, 3, 4, 5].map((i) => <rect key={i} x={19 + i * 11.4} y='49' width='6' height='26' fill={C.marble} />)}
      <rect x='14' y='76' width='72' height='4' fill={C.marble} />
      <rect x='10' y='81' width='80' height='4' fill={C.marble} />
    </>
  ),
  column: (
    <>
      <Badge fill={C.sky} />
      <circle cx='36' cy='30' r='7' fill={C.marble} />
      <circle cx='64' cy='30' r='7' fill={C.marble} />
      <rect x='36' y='25' width='28' height='9' fill={C.marble} />
      <rect x='40' y='34' width='20' height='46' fill={C.marble} />
      {[44, 50, 56].map((x) => <line key={x} x1={x} y1='36' x2={x} y2='78' stroke='#cfc6b4' strokeWidth='1.5' />)}
      <rect x='33' y='80' width='34' height='6' fill={C.marble} />
    </>
  ),
  owl: (
    <>
      <Badge fill={C.night} />
      <polygon points='30,26 34,14 42,24' fill='#b5763a' />
      <polygon points='70,26 66,14 58,24' fill='#b5763a' />
      <ellipse cx='50' cy='56' rx='25' ry='29' fill='#b5763a' />
      <ellipse cx='50' cy='64' rx='14' ry='18' fill='#e8c9a0' />
      <circle cx='40' cy='44' r='10' fill='#fff' />
      <circle cx='60' cy='44' r='10' fill='#fff' />
      <circle cx='40' cy='44' r='4.5' fill={C.night} />
      <circle cx='60' cy='44' r='4.5' fill={C.night} />
      <polygon points='46,50 54,50 50,58' fill={C.gold} />
    </>
  ),
  wreath: (
    <>
      <Badge fill={C.marble} />
      {[30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((a) => (
        <ellipse key={a} cx='50' cy='19' rx='5' ry='11' fill={a % 60 ? C.olive : '#5a7b2d'} transform={`rotate(${a} 50 50)`} />
      ))}
      <circle cx='50' cy='50' r='9' fill={C.gold} />
    </>
  ),
  amphora: (
    <>
      <Badge fill={C.gold} />
      <path d='M38 26 C28 26 26 40 34 46 M62 26 C72 26 74 40 66 46' stroke={C.clay} strokeWidth='4' fill='none' />
      <path d='M40 18 h20 v8 c10 4 14 14 12 28 c-2 14 -10 22 -22 24 c-12 -2 -20 -10 -22 -24 c-2 -14 2 -24 12 -28 z' fill={C.clay} />
      <rect x='30' y='46' width='40' height='6' fill={C.night} opacity='.8' />
      <rect x='40' y='78' width='20' height='6' fill={C.clay} />
    </>
  ),
  meander: (
    <>
      <Badge fill={C.clay} />
      <g stroke={C.marble} strokeWidth='5' fill='none' strokeLinejoin='miter'>
        <path d='M14 66 H30 V46 H46 V60 H38 V53' />
        <path d='M54 66 H70 V46 H86 V60 H78 V53' />
        <line x1='14' y1='34' x2='86' y2='34' />
      </g>
    </>
  ),
  lycabettus: (
    <>
      <Badge fill={C.sky} />
      <path d='M6 80 Q50 8 94 80 Z' fill={C.olive} />
      <rect x='44' y='26' width='12' height='9' fill={C.marble} />
      <polygon points='42,26 50,19 58,26' fill={C.clay} />
      <path d='M6 80 H94 A47 47 0 0 1 6 80 Z' fill={C.aegean} opacity='.9' />
    </>
  ),
  tram: (
    <>
      <Badge fill={C.night} />
      <path d='M50 34 L44 22 H60' stroke={C.marble} strokeWidth='2.5' fill='none' />
      <rect x='18' y='34' width='64' height='34' rx='8' fill={C.marble} />
      {[24, 42, 60].map((x) => <rect key={x} x={x} y='40' width='14' height='12' rx='2' fill={C.aegean} />)}
      <rect x='18' y='56' width='64' height='5' fill={C.clay} />
      <circle cx='32' cy='72' r='5' fill={C.marble} />
      <circle cx='68' cy='72' r='5' fill={C.marble} />
    </>
  ),
  coffee: (
    <>
      <Badge fill={C.clay} />
      <path d='M26 44 h40 v14 a16 16 0 0 1 -16 16 h-8 a16 16 0 0 1 -16 -16 z' fill={C.marble} />
      <path d='M66 48 h4 a7 7 0 0 1 0 14 h-5' stroke={C.marble} strokeWidth='4' fill='none' />
      <rect x='28' y='46' width='36' height='5' fill={C.night} opacity='.8' />
      <path d='M40 36 c-4 -5 4 -8 0 -13 M52 36 c-4 -5 4 -8 0 -13' stroke={C.marble} strokeWidth='3' fill='none' strokeLinecap='round' />
    </>
  ),
  stadium: (
    <>
      <Badge fill={C.olive} />
      <path d='M22 78 V44 a28 28 0 0 1 56 0 V78' stroke={C.marble} strokeWidth='9' fill='none' />
      <path d='M34 78 V46 a16 16 0 0 1 32 0 V78' stroke={C.gold} strokeWidth='4' fill='none' />
      <line x1='16' y1='78' x2='84' y2='78' stroke={C.marble} strokeWidth='5' />
    </>
  ),
  helmet: (
    <>
      <Badge fill={C.aegean} />
      <path d='M32 24 C34 12 62 8 74 20' stroke={C.clay} strokeWidth='6' fill='none' strokeLinecap='round' />
      <path d='M26 64 C26 36 40 26 54 26 C70 26 76 40 74 56 L70 72 H60 L58 62 C52 64 44 64 38 68 L36 76 H28 Z' fill={C.gold} />
      <path d='M44 48 h14 v6 h-14 z' fill={C.night} />
    </>
  ),
  cat: (
    <>
      <Badge fill={C.gold} />
      <path d='M64 78 C84 78 86 56 74 52' stroke={C.night} strokeWidth='6' fill='none' strokeLinecap='round' />
      <ellipse cx='50' cy='62' rx='17' ry='21' fill={C.night} />
      <circle cx='50' cy='36' r='13' fill={C.night} />
      <polygon points='38,30 40,15 49,25' fill={C.night} />
      <polygon points='62,30 60,15 51,25' fill={C.night} />
      <circle cx='45' cy='36' r='2.6' fill={C.gold} />
      <circle cx='55' cy='36' r='2.6' fill={C.gold} />
    </>
  ),
  word: (
    <>
      <rect x='4' y='22' width='92' height='56' rx='14' fill={C.marble} />
      <rect x='9' y='27' width='82' height='46' rx='10' fill='none' stroke={C.aegean} strokeWidth='2.5' />
      <text x='50' y='58' textAnchor='middle' fontSize='23' fontWeight='800' fill={C.aegean} fontFamily='system-ui, sans-serif'>ΑΘΗΝΑ</text>
    </>
  ),
};

// left/top in %, size in px, rot in degrees
const STICKERS = [
  { art: 'parthenon', left: 3, top: 5, size: 160, rot: -8 },
  { art: 'owl', left: 80, top: 4, size: 130, rot: 10 },
  { art: 'amphora', left: 2, top: 34, size: 118, rot: 9 },
  { art: 'column', left: 88, top: 31, size: 110, rot: -6 },
  { art: 'lycabettus', left: 4, top: 72, size: 150, rot: 6 },
  { art: 'tram', left: 72, top: 74, size: 150, rot: -7 },
  { art: 'word', left: 21, top: 6, size: 140, rot: -4 },
  { art: 'wreath', left: 44, top: 1, size: 112, rot: 6 },
  { art: 'helmet', left: 79, top: 52, size: 120, rot: -5 },
  { art: 'meander', left: 14, top: 55, size: 100, rot: -10 },
  { art: 'coffee', left: 45, top: 86, size: 104, rot: 8 },
  { art: 'stadium', left: 22, top: 80, size: 118, rot: -6 },
  { art: 'cat', left: 89, top: 85, size: 94, rot: 7 },
];

const stickerStyle = (s, i) => ({
  left: `${s.left}%`,
  top: `${s.top}%`,
  width: `clamp(56px, ${s.size * 0.08}vw, ${s.size}px)`,
  '--r': `${s.rot}deg`,
  transform: 'rotate(var(--r))',
  animationDelay: `${i * 70}ms`,
})

// On phones only the first 8 stickers show; no slap animation with reduced motion
const STICKER_CLASS = 'absolute h-auto sticker-outline animate-slap motion-reduce:animate-none max-sm:nth-[n+9]:hidden'

// Realistic stickers: drop transparent PNGs into /public/stickers, named after
// each key above (parthenon.png, owl.png, …). Any file that is missing falls
// back to the drawn version.
function Sticker({ s, i }) {
  const [failed, setFailed] = useState(false)
  const style = stickerStyle(s, i)
  if (failed) {
    return (
      <svg className={STICKER_CLASS} viewBox='0 0 100 100' style={style}>
        {ART[s.art]}
      </svg>
    )
  }
  return <img className={STICKER_CLASS} src={`/stickers/${s.art}.png`} alt='' style={style} onError={() => setFailed(true)} />
}

export default function StickerBomb() {
  return (
    <div className='pointer-events-none fixed inset-0 z-[1] overflow-hidden' aria-hidden='true'>
      {STICKERS.map((s, i) => (
        <Sticker key={s.art} s={s} i={i} />
      ))}
    </div>
  )
}
