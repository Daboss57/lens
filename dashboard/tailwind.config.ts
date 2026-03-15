import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0b1020',
        panel: '#111831',
        panelSoft: '#172240',
        line: '#273458',
        highlight: '#64d2ff',
        signal: '#f97316',
        lime: '#7dd3a7',
        rose: '#fb7185',
        text: '#e8eefc',
        muted: '#9badcf',
      },
      fontFamily: {
        sans: ['Space Grotesk', 'Segoe UI', 'sans-serif'],
        mono: ['IBM Plex Mono', 'Consolas', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(100, 210, 255, 0.16), 0 18px 50px rgba(7, 11, 23, 0.45)',
      },
      backgroundImage: {
        grid: 'linear-gradient(rgba(157,173,207,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(157,173,207,0.08) 1px, transparent 1px)',
      },
    },
  },
  plugins: [],
} satisfies Config
