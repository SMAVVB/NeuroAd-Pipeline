'use client'

import { DashboardProvider } from '@/lib/dashboard-context'
import { Sidebar } from '@/components/sidebar'

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <DashboardProvider>
      <div className="min-h-screen bg-background">
        <Sidebar />
        <main className="lg:pl-[260px] min-h-screen">
          <div className="p-6 lg:p-8 max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </DashboardProvider>
  )
}
