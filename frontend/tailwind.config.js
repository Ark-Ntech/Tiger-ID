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
        // Primary tactical colors - professional, authoritative
        primary: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        // Tactical slate-based palette
        tactical: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        // Tiger accent colors - for critical alerts and branding
        tiger: {
          orange: '#ff6b35',
          'orange-dark': '#e55a2b',
          'orange-light': '#ff8c5a',
          black: '#1a1a1a',
          cream: '#f4e8d8',
        },
        // Status colors - semantic meanings
        status: {
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
          info: '#3b82f6',
          neutral: '#6b7280',
        },
        // Evidence-specific colors
        evidence: {
          high: '#059669',
          medium: '#d97706',
          low: '#ea580c',
          critical: '#dc2626',
        },
      },
      fontFamily: {
        sans: ['DM Sans', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        display: ['DM Sans', 'Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.3s ease-out forwards',
        'fade-in-down': 'fadeInDown 0.3s ease-out forwards',
        'slide-in-right': 'slideInRight 0.3s ease-out forwards',
        'slide-in-left': 'slideInLeft 0.3s ease-out forwards',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'scale-in': 'scaleIn 0.2s ease-out forwards',
        'progress': 'progress 1.5s ease-in-out infinite',
        'shimmer': 'shimmer 1.5s infinite',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(255, 107, 53, 0.4)' },
          '50%': { boxShadow: '0 0 0 8px rgba(255, 107, 53, 0)' },
        },
        progress: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
      boxShadow: {
        // Tactical shadows
        'tactical': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'tactical-md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'tactical-lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        // Evidence card shadows
        'evidence': '0 4px 14px 0 rgba(16, 185, 129, 0.15), 0 2px 6px -1px rgba(16, 185, 129, 0.1)',
        'evidence-hover': '0 8px 25px 0 rgba(16, 185, 129, 0.2), 0 4px 10px -2px rgba(16, 185, 129, 0.15)',
        // Critical alert shadows
        'critical': '0 4px 14px 0 rgba(239, 68, 68, 0.2), 0 2px 6px -1px rgba(239, 68, 68, 0.15)',
        'critical-hover': '0 8px 25px 0 rgba(239, 68, 68, 0.25), 0 4px 10px -2px rgba(239, 68, 68, 0.2)',
        // Match card shadows
        'match': '0 4px 14px 0 rgba(59, 130, 246, 0.15), 0 2px 6px -1px rgba(59, 130, 246, 0.1)',
        'match-hover': '0 8px 25px 0 rgba(59, 130, 246, 0.2), 0 4px 10px -2px rgba(59, 130, 246, 0.15)',
        // Tiger orange glow
        'tiger': '0 4px 14px 0 rgba(255, 107, 53, 0.2), 0 2px 6px -1px rgba(255, 107, 53, 0.15)',
        'tiger-glow': '0 0 20px rgba(255, 107, 53, 0.3)',
        // Inner shadows for depth
        'inner-soft': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
        'inner-card': 'inset 0 1px 2px 0 rgb(0 0 0 / 0.05)',
      },
      backgroundImage: {
        // Tactical gradients
        'tactical-gradient': 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        'tactical-gradient-light': 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        // Alert gradients
        'alert-warning': 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
        'alert-critical': 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)',
        'alert-success': 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)',
        // Tiger gradient
        'tiger-gradient': 'linear-gradient(135deg, #ff6b35 0%, #e55a2b 100%)',
        // Verification gradient
        'verification-gradient': 'linear-gradient(135deg, #eff6ff 0%, #f3e8ff 100%)',
      },
      borderRadius: {
        'tactical': '0.625rem',
        '4xl': '2rem',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },
      transitionDuration: {
        '400': '400ms',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
