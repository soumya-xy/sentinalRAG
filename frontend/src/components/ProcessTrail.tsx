export function ProcessTrail({
  steps,
}: {
  steps: { title: string; body: string }[]
}) {
  return (
    <ol className="mt-6 w-full max-w-md space-y-3 text-left">
      {steps.map((step, index) => (
        <li key={step.title} className="flex gap-3">
          <span className="font-mono text-[10px] text-[#777777] w-5 shrink-0 pt-0.5">
            {String(index + 1).padStart(2, '0')}
          </span>
          <div>
            <div className="text-xs text-[#DDDDDD]">{step.title}</div>
            <p className="mt-0.5 text-xs text-[#888888] leading-relaxed">{step.body}</p>
          </div>
        </li>
      ))}
    </ol>
  )
}
