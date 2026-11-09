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
        // Pure Charcoal & Neutral Grey Palette (Zero Blue / Slate undertones)
        obsidian: {
          950: '#060708', // Deepest background
          900: '#090a0c', // Main root background
          850: '#121316', // Card surface
          800: '#1a1b1f', // Elevated panel
          750: '#23252a', // Subtle interactive surface
          700: '#282a2e', // Structural border
          600: '#36383f', // Hover border
          500: '#52555e', // Subtle icon / line
          400: '#8c8e96', // Muted secondary text
          300: '#b4b6be', // Primary muted text
          200: '#d9dade', // High-contrast text
          100: '#f4f4f5', // Crisp white text
        },
        // Restrained Status Indicators (Functional Only)
        status: {
          pass: '#10b981',       // Compliant / Verified (Emerald)
          'pass-bg': '#06281e',  // Muted background
          review: '#f59e0b',     // Review Required / Warning (Amber)
          'review-bg': '#2a1b05',// Muted background
          fail: '#ef4444',       // Confirmed Breach / Rejected (Crimson)
          'fail-bg': '#290c0c',  // Muted background
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      }
    },
  },
  plugins: [],
};
