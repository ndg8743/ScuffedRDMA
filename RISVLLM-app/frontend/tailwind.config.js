/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        ide: {
          bg: '#0d1117',
          surface: '#161b22',
          border: '#30363d',
          hover: '#1f2937',
          accent: '#58a6ff',
          accentDim: '#388bfd33',
          green: '#3fb950',
          red: '#f85149',
          orange: '#d29922',
          purple: '#bc8cff',
          text: '#e6edf3',
          textDim: '#8b949e',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', '"SF Mono"', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
};
