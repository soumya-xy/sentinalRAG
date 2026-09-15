export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="border border-critical/70 bg-critical/10 px-3 py-2 text-sm text-ink">
      {message}
    </div>
  )
}
