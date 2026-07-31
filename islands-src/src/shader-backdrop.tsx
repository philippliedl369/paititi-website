import { StrictMode, useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Shader, Swirl, ChromaFlow, FlutedGlass, FilmGrain } from 'shaders/react'

// Meristem brand values (mirrors the site's _ds tokens; kept inline so this island
// is self-contained and needs no build wiring into the design system).
const BRAND = {
  mist: '#F5F7FA',
  amber: '#2DD4BF',
  copper: '#0C7C59',
}

/**
 * Meristem animated shader backdrop — "from chaos, comes clarity".
 *
 * The backdrop loads visibly turbulent and settles, once, into a near-still
 * calm state. The motion has a beginning and an end (no loop), matching the
 * design system's motion rules and enacting the tagline.
 *
 * Usage in any .dc.html / .html page:
 *   <div data-island="shader-backdrop" style="position:absolute;inset:0"></div>
 *   <script type="module" src="/islands/shader-backdrop.js" defer></script>
 *
 * The parent must be position:relative; the backdrop fills it, sits behind the
 * content, and never captures pointer events.
 *
 * Optional data attributes:
 *   data-warm       accent hex for the warm flow   (default: brand amber)
 *   data-warm-2     secondary accent hex           (default: brand copper)
 *   data-hold-ms    how long to stay chaotic       (default: 700)
 *   data-settle-ms  duration of the settle         (default: 7300)
 *   data-static     "true" renders the calm end state with no settle
 *
 * Live-tuning API (used by islands-playground.html):
 *   MeristemIslands.tuneShaderBackdrop(el, {calm?, chaos?, colors?, holdMs?, settleMs?})
 *   MeristemIslands.replayShaderBackdrop(el)
 *   MeristemIslands.holdShaderBackdrop(el, 'chaos' | 'calm')
 *   MeristemIslands.shaderBackdropDefaults  — the CALM/CHAOS presets
 */

interface Params {
  swirlSpeed: number
  swirlDetail: number
  momentum: number
  radius: number
  frequency: number
  angle: number
  refraction: number
  aberration: number
  waveAmplitude: number
  waveFrequency: number
  flutedSpeed: number
  highlight: number
  softness: number
  grain: number
}

// The resting state: the original brand-calibrated backdrop, slowed to near-still.
const CALM: Params = {
  swirlSpeed: 0.35,
  swirlDetail: 1.7,
  momentum: 13,
  radius: 3.5,
  frequency: 8,
  angle: 31,
  refraction: 4,
  aberration: 0.61,
  waveAmplitude: 0.06,
  waveFrequency: 1.5,
  flutedSpeed: 0.15,
  highlight: 0.12,
  softness: 1,
  grain: 0.05,
}

// The opening state: same layers pushed toward the top of their ranges
// (momentum caps at 60, radius at 5) so the first frame reads as turbulence.
const CHAOS: Params = {
  swirlSpeed: 2.6,
  swirlDetail: 3.6,
  momentum: 52,
  radius: 4.9,
  frequency: 8,
  angle: 31,
  refraction: 6.5,
  aberration: 1.5,
  waveAmplitude: 0.32,
  waveFrequency: 2.5,
  flutedSpeed: 0.85,
  highlight: 0.2,
  softness: 1,
  grain: 0.15,
}

interface Colors {
  warm: string
  warm2: string
  mist: string
}

interface Config {
  colors: Colors
  chaos: Params
  calm: Params
  holdMs: number
  settleMs: number
}

interface Controller {
  tune: (patch: Partial<{ [K in 'chaos' | 'calm']: Partial<Params> } & { colors: Partial<Colors>; holdMs: number; settleMs: number }>) => void
  replay: () => void
  hold: (state: 'chaos' | 'calm') => void
}

const easeInOutCubic = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)

function lerpParams(a: Params, b: Params, t: number): Params {
  const out = {} as Params
  for (const k of Object.keys(a) as (keyof Params)[]) out[k] = a[k] + (b[k] - a[k]) * t
  return out
}

const prefersReducedMotion = () =>
  typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches

function ShaderBackdrop({ initial, isStatic, onReady }: { initial: Config; isStatic: boolean; onReady: (c: Controller) => void }) {
  const [cfg, setCfg] = useState(initial)
  const [t, setT] = useState(isStatic || prefersReducedMotion() ? 1 : 0)
  const cfgRef = useRef(cfg)
  cfgRef.current = cfg
  const raf = useRef(0)
  const runSeq = useRef(0)

  const play = () => {
    cancelAnimationFrame(raf.current)
    if (isStatic || prefersReducedMotion()) {
      setT(1)
      return
    }
    const seq = ++runSeq.current
    const start = performance.now()
    const tick = (now: number) => {
      if (seq !== runSeq.current) return
      const { holdMs, settleMs } = cfgRef.current
      const elapsed = now - start
      if (elapsed < holdMs) {
        setT(0)
      } else {
        const p = Math.min(1, (elapsed - holdMs) / Math.max(1, settleMs))
        setT(easeInOutCubic(p))
        if (p >= 1) return
      }
      raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
  }

  useEffect(() => {
    play()
    onReady({
      tune: (patch) =>
        setCfg((prev) => ({
          ...prev,
          ...(patch.holdMs !== undefined ? { holdMs: patch.holdMs } : null),
          ...(patch.settleMs !== undefined ? { settleMs: patch.settleMs } : null),
          colors: { ...prev.colors, ...patch.colors },
          chaos: { ...prev.chaos, ...patch.chaos },
          calm: { ...prev.calm, ...patch.calm },
        })),
      replay: play,
      hold: (state) => {
        runSeq.current++
        cancelAnimationFrame(raf.current)
        setT(state === 'chaos' ? 0 : 1)
      },
    })
    return () => cancelAnimationFrame(raf.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const p = lerpParams(cfg.chaos, cfg.calm, t)
  const { warm, warm2, mist } = cfg.colors

  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
      <Shader style={{ width: '100%', height: '100%' }}>
        <Swirl colorA="#ffffff" colorB={mist} detail={p.swirlDetail} speed={p.swirlSpeed} />
        <ChromaFlow
          baseColor="#ffffff"
          downColor={warm}
          leftColor={warm2}
          rightColor={warm}
          upColor={warm2}
          momentum={p.momentum}
          radius={p.radius}
        />
        <FlutedGlass
          aberration={p.aberration}
          angle={p.angle}
          frequency={p.frequency}
          highlight={p.highlight}
          highlightSoftness={0}
          lightAngle={-90}
          refraction={p.refraction}
          shape="rounded"
          softness={p.softness}
          speed={p.flutedSpeed}
          waveAmplitude={p.waveAmplitude}
          waveFrequency={p.waveFrequency}
        />
        <FilmGrain strength={p.grain} />
      </Shader>
    </div>
  )
}

const controllers = new Map<Element, Controller>()

function mount(el: Element) {
  if (el.getAttribute('data-island-mounted') === 'true') return
  el.setAttribute('data-island-mounted', 'true')
  const num = (name: string, fallback: number) => {
    const v = Number(el.getAttribute(name))
    return Number.isFinite(v) && el.getAttribute(name) !== null ? v : fallback
  }
  const initial: Config = {
    colors: {
      warm: el.getAttribute('data-warm') || BRAND.amber,
      warm2: el.getAttribute('data-warm-2') || BRAND.copper,
      mist: BRAND.mist,
    },
    chaos: { ...CHAOS },
    calm: { ...CALM },
    holdMs: num('data-hold-ms', 700),
    settleMs: num('data-settle-ms', 7300),
  }
  const isStatic = el.getAttribute('data-static') === 'true'
  createRoot(el).render(
    <StrictMode>
      <ShaderBackdrop initial={initial} isStatic={isStatic} onReady={(c) => controllers.set(el, c)} />
    </StrictMode>,
  )
}

function mountAll() {
  document.querySelectorAll('[data-island="shader-backdrop"]').forEach(mount)
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountAll)
} else {
  mountAll()
}

// Explicit API for pages that inject the target element after load, and for
// the tuning playground.
declare global {
  interface Window {
    MeristemIslands?: {
      mountShaderBackdrop: (el: Element) => void
      tuneShaderBackdrop: (el: Element, patch: Parameters<Controller['tune']>[0]) => void
      replayShaderBackdrop: (el: Element) => void
      holdShaderBackdrop: (el: Element, state: 'chaos' | 'calm') => void
      shaderBackdropDefaults: { calm: Params; chaos: Params; colors: Colors; holdMs: number; settleMs: number }
    }
  }
}
window.MeristemIslands = {
  ...(window.MeristemIslands || {}),
  mountShaderBackdrop: mount,
  tuneShaderBackdrop: (el, patch) => controllers.get(el)?.tune(patch),
  replayShaderBackdrop: (el) => controllers.get(el)?.replay(),
  holdShaderBackdrop: (el, state) => controllers.get(el)?.hold(state),
  shaderBackdropDefaults: {
    calm: { ...CALM },
    chaos: { ...CHAOS },
    colors: { warm: BRAND.amber, warm2: BRAND.copper, mist: BRAND.mist },
    holdMs: 700,
    settleMs: 7300,
  },
}
