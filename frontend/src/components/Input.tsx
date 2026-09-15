import type { InputHTMLAttributes, TextareaHTMLAttributes } from 'react'

const fieldClass =
  'w-full border border-border bg-base px-3 py-2 text-ink outline-none placeholder:text-muted/70 focus:border-sage'

export function Input({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`${fieldClass} ${className}`} {...props} />
}

export function TextArea({ className = '', ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`${fieldClass} resize-y min-h-[88px] ${className}`} {...props} />
}
