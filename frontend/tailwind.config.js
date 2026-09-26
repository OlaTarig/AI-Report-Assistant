/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          orange: "#FF971D",
          "orange-dark": "#E0800A",
          peach: "#FFE8D6",
          offwhite: "#F9F6F7",
          white: "#FFFFFF",
        },
      },
    },
  },
  plugins: [],
};