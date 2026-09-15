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
      <div className="min-h-screen bg-base px-8 py-8 font-mono text-sm text-muted">
        Restoring session…
      </div>
    )
  }
  return children
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
