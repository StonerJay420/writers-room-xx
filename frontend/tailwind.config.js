/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'neon-purple': '#bf00ff',
        'neon-cyan': '#00ffff',
        'neon-pink': '#ff00ff',
        'neon-green': '#00ff88',
        'neon-yellow': '#ffff00',
        'neon-orange': '#ff8800',
        'dark-bg': '#0a0a0f',
        'dark-surface': '#12121a',
        'dark-border': '#1a1a28',
      },
      boxShadow: {
        'neon-purple': '0 0 20px rgba(191, 0, 255, 0.5)',
        'neon-cyan': '0 0 20px rgba(0, 255, 255, 0.5)',
        'neon-pink': '0 0 20px rgba(255, 0, 255, 0.5)',
        'neon-green': '0 0 20px rgba(0, 255, 136, 0.5)',
        'neon-glow': '0 0 30px rgba(191, 0, 255, 0.3)',
      },
      animation: {
        'pulse-neon': 'pulse-neon 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        'pulse-neon': {
          '0%, 100%': {
            opacity: 1,
            boxShadow: '0 0 20px rgba(191, 0, 255, 0.5)',
          },
          '50%': {
            opacity: 0.8,
            boxShadow: '0 0 30px rgba(191, 0, 255, 0.8)',
          },
        },
        'glow': {
          'from': {
            textShadow: '0 0 10px rgba(191, 0, 255, 0.5), 0 0 20px rgba(191, 0, 255, 0.5)',
          },
          'to': {
            textShadow: '0 0 20px rgba(191, 0, 255, 0.8), 0 0 30px rgba(191, 0, 255, 0.8)',
          },
        },
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
        'display': ['Orbitron', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
