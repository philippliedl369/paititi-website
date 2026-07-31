import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'node:path'

// Each island builds into a self-contained ES-module bundle (its own React
// included) in ../islands/, where it is committed and served by nginx as a
// plain static asset — the static site itself stays zero-build.
//
// Islands are built ONE AT A TIME (single entry per Vite run, selected by the
// ISLAND env var) so Rollup never hoists a shared React chunk across them and
// every bundle stays a single self-contained file. `npm run build` runs this
// once per island in sequence.
const ENTRIES: Record<string, string> = {
  'shader-backdrop': resolve(__dirname, 'src/shader-backdrop.tsx'),
}

const island = process.env.ISLAND
if (island && !ENTRIES[island]) {
  throw new Error(
    `Unknown ISLAND "${island}". Known: ${Object.keys(ENTRIES).join(', ')}`
  )
}
const entry = island ? { [island]: ENTRIES[island] } : ENTRIES

export default defineConfig({
  plugins: [react()],
  // Lib builds don't auto-replace process.env, and the bundle runs in a plain
  // page with no bundler shims — pin it so React ships its production build.
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
  build: {
    outDir: resolve(__dirname, '../islands'),
    // Only wipe on the first island of the sequence (EMPTY=1); later
    // single-island builds append rather than deleting the earlier bundles.
    emptyOutDir: process.env.EMPTY === '1',
    lib: {
      entry,
      formats: ['es'],
    },
    rollupOptions: {
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name][extname]',
      },
    },
  },
})
