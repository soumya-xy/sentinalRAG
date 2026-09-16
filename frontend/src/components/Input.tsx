import type { InputHTMLAttributes, TextareaHTMLAttributes } from 'react'

const baseInput = [
  'w-full bg-[#0a0a0a] border border-[#333333] text-[#EEEEEE]',
  'placeholder:text-[#999999]',
  'focus:outline-none focus:border-[#CB2957]',
  'transition-colors duration-150',
  'rounded-sm px-3 py-2 text-sm font-mono',
].join(' ')

export function Input({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`${baseInput} h-9 ${className}`} {...props} />
}

export function TextArea({ className = '', ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      rows={4}
      className={`${baseInput} resize-none py-3 ${className}`}
      {...props}
    />
  )
}
