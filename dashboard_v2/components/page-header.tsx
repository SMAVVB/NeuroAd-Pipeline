'use client'

import { useDashboard } from '@/lib/dashboard-context'

interface PageHeaderProps {
  title: string
  description?: string
  showCampaignInfo?: boolean
}

// Transform campaign name: "apple_vs_samsung" -> "Apple vs Samsung"
function formatCampaignName(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function PageHeader({ title, description, showCampaignInfo = true }: PageHeaderProps) {
  const { selectedCampaign, selectedBrand } = useDashboard()

  return (
    <div className="mb-8">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      {description && (
        <p className="text-muted-foreground mt-1">{description}</p>
      )}
      {showCampaignInfo && selectedCampaign && (
        <div className="flex items-center gap-2 mt-3 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">{formatCampaignName(selectedCampaign.name)}</span>
          <span>•</span>
          <span>{selectedBrand?.name}</span>
          <span>•</span>
          <span>{new Date(selectedCampaign.date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}</span>
        </div>
      )}
    </div>
  )
}
