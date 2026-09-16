import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AuthPage } from './features/auth/AuthPage.tsx'
import { LandingPage } from './features/landing/LandingPage.tsx'
import { WorkspacePage } from './features/workspace/WorkspacePage.tsx'
import { AuthProvider, useAuth } from './lib/auth.tsx'

function SessionGate({ children }: { children: ReactNode }) {
  const { ready } = useAuth()
  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-black">
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-[#CB2957]">
            <svg width="18" height="18" viewBox="0 0 14 14" fill="none">
              <rect x="0" y="3" width="9" height="8" rx="1.2" fill="white"/>
              <path d="M9 5.5l4.5-2.5v8l-4.5-2.5V5.5z" fill="white"/>
            </svg>
          </div>
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#888888]">
            Restoring session…
          </span>
        </div>
      </div>
    )
  }
  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <SessionGate>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/auth" element={<AuthPage />} />
            <Route path="/workspace" element={<WorkspacePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </SessionGate>
      </BrowserRouter>
    </AuthProvider>
  )
}
