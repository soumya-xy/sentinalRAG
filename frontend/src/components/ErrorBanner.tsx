interface Props {
  message: string
}

export function ErrorBanner({ message }: Props) {
  return (
    <div className="flex items-start gap-3 rounded-sm border border-[#CB2957]/40 bg-[#CB2957]/10 px-4 py-3">
      <span className="mt-0.5 shrink-0 text-[#CB2957]">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <circle cx="7" cy="7" r="6.5" stroke="currentColor"/>
          <path d="M7 4v3.5M7 9.5h.008" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
        </svg>
      </span>
      <p className="text-sm text-[#DDDDDD] font-mono leading-relaxed">{message}</p>
    </div>
  )
}
