'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useDashboard } from '@/lib/dashboard-context'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import {
  LayoutDashboard,
  Building2,
  Brain,
  Fish,
  Palette,
  Eye,
  FileBarChart,
  Moon,
  Sun,
  Menu,
  X,
} from 'lucide-react'
import { useState } from 'react'

const navItems = [
  { href: '/', label: 'Overview', icon: LayoutDashboard },
  { href: '/brand-intelligence', label: 'Brand Intelligence', icon: Building2 },
  { href: '/tribe', label: 'TRIBE Neural', icon: Brain },
  { href: '/mirofish', label: 'MiroFish Social', icon: Fish },
  { href: '/clip', label: 'CLIP Brand', icon: Palette },
  { href: '/vinet', label: 'ViNet Attention', icon: Eye },
  { href: '/report', label: 'Report & Ranking', icon: FileBarChart },
]

export function Sidebar() {
  const pathname = usePathname()
  const {
    selectedBrandId,
    selectedCampaignId,
    setSelectedBrandId,
    setSelectedCampaignId,
    availableCampaigns,
    isDarkMode,
    toggleDarkMode,
    loading,
  } = useDashboard()
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  return (
    <>
      {/* Mobile toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 lg:hidden"
        onClick={() => setIsMobileOpen(!isMobileOpen)}
      >
        {isMobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      {/* Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-40 h-screen w-[260px] bg-sidebar border-r border-sidebar-border flex flex-col transition-transform duration-200',
          'lg:translate-x-0',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-sidebar-border">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-foreground rounded flex items-center justify-center">
              <span className="text-background font-bold text-sm">N</span>
            </div>
            <span className="font-semibold text-lg tracking-tight">NeuroAd</span>
          </Link>
        </div>

        {/* Selectors */}
        <div className="p-4 space-y-3 border-b border-sidebar-border">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
              Brand
            </label>
            {loading ? (
              <div className="h-10 w-full animate-pulse bg-muted rounded-md" />
            ) : (
              <Select
                value={selectedBrandId || ''}
                onValueChange={(value) => {
                  setSelectedBrandId(value)
                  setSelectedCampaignId(null)
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select brand" />
                </SelectTrigger>
                <SelectContent>
                  {Array.from(new Set(availableCampaigns.map((c) => c.brandId))).map((brandId) => {
                    // Derive brand name from campaign names: "apple_vs_samsung" -> "Apple vs Samsung"
                    const campaignForBrand = availableCampaigns.find((c) => c.brandId === brandId)
                    if (!campaignForBrand) return null
                    const brandName = String(brandId).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
                    return (
                      <SelectItem key={brandId} value={brandId}>
                        <span className="flex items-center gap-2">
                          <span>_brand_</span>
                          <span>{brandName}</span>
                        </span>
                      </SelectItem>
                    )
                  })}
                </SelectContent>
              </Select>
            )}
          </div>

          {true && (
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                Campaign
              </label>
              {loading ? (
                <div className="h-10 w-full animate-pulse bg-muted rounded-md" />
              ) : (
                <Select
                  value={selectedCampaignId || ''}
                  onValueChange={setSelectedCampaignId}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select campaign" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableCampaigns.map((campaign) => (
                      <SelectItem key={campaign.id} value={campaign.id}>
                        {campaign.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsMobileOpen(false)}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* Dark mode toggle */}
        <div className="p-4 border-t border-sidebar-border">
          <Button
            variant="ghost"
            className="w-full justify-start gap-3"
            onClick={toggleDarkMode}
          >
            {isDarkMode ? (
              <>
                <Sun className="h-4 w-4" />
                <span>Light Mode</span>
              </>
            ) : (
              <>
                <Moon className="h-4 w-4" />
                <span>Dark Mode</span>
              </>
            )}
          </Button>
        </div>
      </aside>
    </>
  )
}
