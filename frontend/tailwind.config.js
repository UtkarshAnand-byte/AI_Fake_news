/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          bgDark: '#0b0f19',
          bgLight: '#f4f6fc',
          cardDark: 'rgba(15, 23, 42, 0.45)',
          cardLight: 'rgba(255, 255, 255, 0.65)',
          borderDark: 'rgba(255, 255, 255, 0.08)',
          borderLight: 'rgba(0, 0, 0, 0.08)',
          accent: '#7c3aed', // violet-600
          accentGlow: '#a78bfa', // violet-400
          green: '#10b981', // emerald-500
          red: '#f43f5e', // rose-500
          textDark: '#e2e8f0',
          textLight: '#1e293b'
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'JetBrains Mono', 'monospace']
      },
      boxShadow: {
        'glow-accent': '0 0 20px rgba(124, 58, 237, 0.25)',
        'glow-green': '0 0 20px rgba(16, 185, 129, 0.25)',
        'glow-red': '0 0 20px rgba(244, 63, 94, 0.25)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.3)'
      },
      backdropBlur: {
        xs: '2px',
        md: '12px',
        lg: '24px'
      }
    },
  },
  plugins: [],
}
