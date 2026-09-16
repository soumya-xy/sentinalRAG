import type { ButtonHTMLAttributes } from 'react'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'danger'
  size?: 'sm' | 'md'
}

const variants = {
  primary: [
    'bg-[#CB2957] text-white border border-[#CB2957]',
    'hover:bg-[#a8213e] hover:border-[#a8213e]',
    'disabled:opacity-40 disabled:cursor-not-allowed',
    'transition-all duration-150',
    'shadow-[0_0_16px_rgba(203,41,87,0.3)]',
    'hover:shadow-[0_0_24px_rgba(203,41,87,0.5)]',
  ].join(' '),

  ghost: [
    'bg-transparent text-[#DDDDDD] border border-[#333333]',
    'hover:border-[#CB2957] hover:text-white',
    'disabled:opacity-40 disabled:cursor-not-allowed',
    'transition-all duration-150',
  ].join(' '),

  danger: [
    'bg-transparent text-[#ef4444] border border-[#ef4444]',
    'hover:bg-[#ef4444] hover:text-white',
    'disabled:opacity-40 disabled:cursor-not-allowed',
    'transition-all duration-150',
  ].join(' '),
}

const sizes = {
  sm: 'h-7 px-3 text-xs font-mono tracking-wide uppercase',
  md: 'h-9 px-4 text-sm font-mono tracking-wide uppercase',
}

export function Button({ variant = 'primary', size = 'md', className = '', children, ...rest }: Props) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-sm font-medium ${variants[variant]} ${sizes[size]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  )
}
