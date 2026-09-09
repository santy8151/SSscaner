/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        ssscaner: {
          dark: '#10151c',
          darker: '#05070a',
          primary: '#2ee6ff',
          secondary: '#ffcc00',
          success: '#39ff8c',
          warning: '#ffcc00',
          danger: '#ff2e88',
          accent: '#2ee6ff'
        }
      },
      fontFamily: {
        sans: ['Barlow', 'system-ui', 'sans-serif'],
        display: ['Rajdhani', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace']
      }
    },
  },
  plugins: [],
}
