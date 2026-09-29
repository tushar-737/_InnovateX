/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#12263f',
        saffron: '#e8590c',
        leaf: '#2b8a3e',
        sky: '#1971c2',
        cream: '#fff8f0',
      },
      minHeight: {
        touch: '4.5rem',
      },
    },
  },
  plugins: [],
};
