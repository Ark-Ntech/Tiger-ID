import { InputHTMLAttributes, forwardRef } from 'react'
import { cn } from '../../utils/cn'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, id, name, ...props }, ref) => {
    // Generate a unique ID for the input if not provided
    const inputId = id || name || `input-${Math.random().toString(36).substr(2, 9)}`

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} data-testid="input-label" className="block text-sm font-medium text-tactical-700 dark:text-tactical-300 mb-1">
            {label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          name={name}
          data-testid="input"
          className={cn(
            'w-full px-3 py-2 border rounded-lg transition-colors',
            'bg-white dark:bg-tactical-800',
            'text-tactical-900 dark:text-tactical-100',
            'focus:outline-none focus:ring-2 focus:ring-tiger-orange focus:border-transparent',
            error
              ? 'border-red-500 focus:ring-red-500'
              : 'border-tactical-300 dark:border-tactical-600',
            'disabled:bg-tactical-100 dark:disabled:bg-tactical-700 disabled:cursor-not-allowed',
            className
          )}
          {...props}
        />
        {error && <p data-testid="input-error" className="mt-1 text-sm text-red-600">{error}</p>}
        {helperText && !error && (
          <p className="mt-1 text-sm text-tactical-500 dark:text-tactical-400">{helperText}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input

