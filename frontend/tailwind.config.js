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
        background: '#0a0505',
        surface: {
          DEFAULT: '#150a0a',
          elevated: '#1f0f0f',
        },
        border: {
          DEFAULT: '#3d1414',
          active: '#7a1f1f',
        },
        text: {
          primary: '#f2e8e8',
          secondary: '#a88888',
        },
        accent: {
          red: '#e11d2e',
          'red-hover': '#ff334b',
          'red-glow': 'rgba(225, 29, 46, 0.45)',
          safe: '#2ecc71',
          warning: '#f5a623',
          danger: '#e11d2e',
        },
        hover: {
          border: '#ff4d5a',
          surface: '#251212',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Space Mono', 'ui-monospace', 'monospace'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glow-red': '0 0 15px rgba(225, 29, 46, 0.45)',
        'glow-red-lg': '0 0 25px rgba(225, 29, 46, 0.65)',
        'glow-green': '0 0 15px rgba(46, 204, 113, 0.45)',
      }
    },
  },
  plugins: [],
}
