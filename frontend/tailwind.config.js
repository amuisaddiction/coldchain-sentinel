/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Command Center Charcoal & Deep Navy Palette
        canvas: {
          950: '#06090E', // Deepest canvas background
          900: '#0A0E17', // Main background
          850: '#0F1523', // Elevated panel background
          800: '#141D2E', // Card surface
          750: '#1A253A', // Interactive surface
          700: '#23304A', // Structural border
          600: '#2F4060', // Hover / active border
          500: '#475C85', // Muted icon / outline
        },
        // Electric Cyan & Frost Blue Accents
        cyan: {
          400: '#38BDF8',
          500: '#0EA5E9',
          brand: '#00F2FE',
          glow: 'rgba(0, 242, 254, 0.15)',
        },
        // Functional Status Colors
        status: {
          pass: '#10B981',        // Verified / Safe (Emerald)
          'pass-bg': '#06281E',   // Muted green badge bg
          warning: '#F59E0B',     // Warning / Excursion caution (Amber)
          'warning-bg': '#2A1B05',// Muted amber badge bg
          danger: '#EF4444',      // Critical Breach / Blocked (Crimson)
          'danger-bg': '#290C0C', // Muted crimson badge bg
          info: '#38BDF8',        // Informational Blue
          'info-bg': '#0C2338',   // Muted info badge bg
        },
        obsidian: {
          950: '#06090E',
          900: '#0A0E17',
          850: '#0F1523',
          800: '#141D2E',
          750: '#1A253A',
          700: '#23304A',
          600: '#2F4060',
          500: '#475C85',
          400: '#94A3B8',
          300: '#CBD5E1',
          200: '#E2E8F0',
          100: '#F8FAFC',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      boxShadow: {
        'glow-cyan': '0 0 20px -3px rgba(0, 242, 254, 0.25)',
        'glow-emerald': '0 0 20px -3px rgba(16, 185, 129, 0.25)',
        'glow-crimson': '0 0 20px -3px rgba(239, 68, 68, 0.25)',
        'card-dark': '0 4px 20px -2px rgba(0, 0, 0, 0.5)',
      }
    },
  },
  plugins: [],
};
