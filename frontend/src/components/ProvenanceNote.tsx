export function ProvenanceNote({
  label,
  children,
}: {
  label: string
  children: string
}) {
  return (
    <div className="rounded-sm border border-[#1a1a1a] bg-[#080808] px-3 py-2.5">
      <div className="font-mono text-[9px] uppercase tracking-widest text-[#888888] mb-1">{label}</div>
      <p className="text-xs text-[#AAAAAA] leading-relaxed">{children}</p>
    </div>
  )
}
