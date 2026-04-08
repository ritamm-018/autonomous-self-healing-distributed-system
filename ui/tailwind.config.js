/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                cyber: {
                    dark: '#050510',
                    light: '#0a0a20',
                    primary: '#00f3ff', // Cyan
                    secondary: '#7000ff', // Purple
                    danger: '#ff003c', // Red
                    success: '#00ff9f', // Green
                    warning: '#fcee0a', // Yellow
                }
            },
            fontFamily: {
                mono: ['JetBrains Mono', 'monospace'],
                display: ['Orbitron', 'sans-serif']
            }
        },
    },
    plugins: [],
}
