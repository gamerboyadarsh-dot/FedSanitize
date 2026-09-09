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
        background: '#050508',
        surface: {
          DEFAULT: '#0C1E3E',
          elevated: '#12264D',
        },
        border: {
          DEFAULT: 'rgba(56, 251, 219, 0.15)',
          active: 'rgba(56, 251, 219, 0.5)',
          cyan: '#38FBDB',
          purple: '#8E52F5',
        },
        text: {
          primary: '#E8F1F5',
          secondary: '#7B8AA3',
        },
        primary: {
          DEFAULT: '#38FBDB',
          hover: '#5effe3',
          glow: 'rgba(56, 251, 219, 0.45)',
        },
        secondary: {
          DEFAULT: '#8E52F5',
          hover: '#a26eff',
          glow: 'rgba(142, 82, 245, 0.45)',
        },
        accent: {
          cyan: '#38FBDB',
          purple: '#8E52F5',
          safe: '#20D9A0',
          warning: '#F5A623',
          danger: '#FF3B5C',
          red: '#FF3B5C',
          'red-hover': '#ff637e',
          'red-glow': 'rgba(255, 59, 92, 0.45)',
        },
        hover: {
          border: '#38FBDB',
          surface: '#142952',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Space Mono', 'ui-monospace', 'monospace'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glow-cyan': '0 0 16px rgba(56, 251, 219, 0.5)',
        'glow-cyan-lg': '0 0 24px rgba(56, 251, 219, 0.7)',
        'glow-purple': '0 0 16px rgba(142, 82, 245, 0.5)',
        'glow-red': '0 0 16px rgba(255, 59, 92, 0.5)',
        'glow-green': '0 0 16px rgba(32, 217, 160, 0.5)',
      }
    },
  },
  plugins: [],
}
