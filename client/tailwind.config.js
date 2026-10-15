/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'urban-dark': '#060913',
        'urban-cyan': '#06B6D4',
        'urban-emerald': '#10B981',
        'urban-crimson': '#F43F5E',
        'urban-amber': '#F59E0B',
        'urban-purple': '#8B5CF6',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': {
            opacity: '1',
            boxShadow: '0 0 15px rgba(6, 182, 212, 0.6), 0 0 30px rgba(6, 182, 212, 0.25)',
            borderColor: 'rgba(6, 182, 212, 0.8)',
          },
          '50%': {
            opacity: '0.65',
            boxShadow: '0 0 6px rgba(6, 182, 212, 0.3), 0 0 12px rgba(6, 182, 212, 0.1)',
            borderColor: 'rgba(6, 182, 212, 0.4)',
          },
        },
        'siren-flash': {
          '0%': {
            opacity: '1',
            backgroundColor: '#F43F5E',
            boxShadow: '0 0 25px #F43F5E, 0 0 50px rgba(244, 63, 94, 0.8)',
          },
          '100%': {
            opacity: '0.25',
            backgroundColor: 'transparent',
            boxShadow: '0 0 4px transparent',
          },
        },
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'siren-flash': 'siren-flash 0.5s alternate infinite',
      },
    },
  },
  plugins: [],
};
