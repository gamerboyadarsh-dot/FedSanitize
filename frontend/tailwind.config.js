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
        background: '#000000',
        surface: {
          DEFAULT: '#09090b', // zinc-950
          elevated: '#18181b', // zinc-900
        },
        border: {
          DEFAULT: 'rgba(255, 255, 255, 0.1)',
          active: 'rgba(255, 255, 255, 0.25)',
          cyan: '#38FBDB',
          purple: '#8E52F5',
        },
        text: {
          primary: '#fafafa',
          secondary: '#a1a1aa',
        },
        primary: {
          DEFAULT: '#ffffff',
          hover: '#f4f4f5',
          glow: 'rgba(255, 255, 255, 0.1)',
        },
        secondary: {
          DEFAULT: '#a1a1aa',
          hover: '#d4d4d8',
          glow: 'rgba(161, 161, 170, 0.1)',
        },
        accent: {
          cyan: '#38FBDB', // keep for chart lines
          purple: '#8E52F5',
          safe: '#10b981', // modern emerald
          warning: '#f59e0b', // modern amber
          danger: '#ef4444', // modern red
          red: '#ef4444',
          'red-hover': '#f87171',
          'red-glow': 'rgba(239, 68, 68, 0.15)',
        },
        hover: {
          border: 'rgba(255, 255, 255, 0.2)',
          surface: '#27272a',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Space Mono', 'ui-monospace', 'monospace'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glow-cyan': '0 0 16px rgba(56, 251, 219, 0.1)',
        'glow-cyan-lg': '0 0 24px rgba(56, 251, 219, 0.2)',
        'glow-purple': '0 0 16px rgba(142, 82, 245, 0.1)',
        'glow-red': '0 0 16px rgba(255, 59, 92, 0.1)',
        'glow-green': '0 0 16px rgba(32, 217, 160, 0.1)',
      }
    },
  },
  plugins: [],
}
