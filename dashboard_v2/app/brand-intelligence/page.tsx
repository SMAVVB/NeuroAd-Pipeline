'use client'

import { DashboardLayout } from '@/components/dashboard-layout'
import { PageHeader } from '@/components/page-header'
import { useDashboard } from '@/lib/dashboard-context'
import { brandIntelligence } from '@/lib/data'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Building2, Globe, Users, Calendar, ExternalLink, RefreshCw, X } from 'lucide-react'
import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkRehype from 'remark-rehype'

// Dynamic import for markdown rendering to avoid SSR issues with remark plugins
const MarkdownContent = dynamic(() => Promise.resolve(({ content }: { content: string }) => (
  <div className="prose prose-sm max-w-none text-foreground">
    <ReactMarkdown remarkPlugins={[remarkGfm, remarkRehype]}>{content}</ReactMarkdown>
  </div>
)), {
  ssr: false,
})

interface BrandReport {
  filename: string
  path: string
  content: string
}

interface BrandResearch {
  brand: string
  founding_year: number
  size: string
  size_reasoning: string
  primary_markets: Array<{ country: string; language: string; depth: string }>
  active_languages: string[]
  industry: string
  sub_industries: string[]
  key_competitors: string[]
  historical_periods: Array<{ label: string; from_year: number; to_year: number; priority: string }>
  query_volume?: { pillars: number; queries_per_pillar: number; social_depth: string }
  validation_notes?: string
  _source_file?: {
    filename: string
    path: string
    type: string
    last_modified: number
    last_modified_iso: string
  }
}

function BrandIntelligenceContent() {
  const { selectedBrandId } = useDashboard()
  const [brandReport, setBrandReport] = useState<BrandReport | null>(null)
  const [brandResearch, setBrandResearch] = useState<BrandResearch | null>(null)
  const [isLoadingReport, setIsLoadingReport] = useState(false)
  const [isLoadingResearch, setIsLoadingResearch] = useState(false)
  const [isReportModalOpen, setIsReportModalOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastResearchRun, setLastResearchRun] = useState<string | null>(null)

  // Existing brand data from lib/data.ts (fallback when API unavailable)
  const existingBrand = selectedBrandId ? brandIntelligence[selectedBrandId as keyof typeof brandIntelligence] : null

  // Fetch STORM report from FastAPI
  useEffect(() => {
    const fetchBrandReport = async () => {
      if (!selectedBrandId) return

      setIsLoadingReport(true)
      setError(null)

      try {
        const response = await fetch(`/api/campaigns/${selectedBrandId}/brand`)
        if (response.ok) {
          const data = await response.json()
          setBrandReport(data)
          // Extract last modified date from response if available
          if (data.last_modified || data.last_modified_iso) {
            setLastResearchRun(data.last_modified_iso || new Date(data.last_modified * 1000).toISOString())
          }
        }
      } catch (err) {
        console.error('Failed to fetch brand report:', err)
        setError('Could not load STORM report')
      } finally {
        setIsLoadingReport(false)
      }
    }

    fetchBrandReport()
  }, [selectedBrandId])

  // Fetch Brand Research JSON from FastAPI
  useEffect(() => {
    const fetchBrandResearch = async () => {
      if (!selectedBrandId) return

      setIsLoadingResearch(true)

      try {
        // Check if brand_profile.json exists in campaign directory
        const response = await fetch(`/api/campaigns/${selectedBrandId}/brand-profile`)
        if (response.ok) {
          const data: BrandResearch = await response.json()
          setBrandResearch(data)
          // Extract last modified date from response if available
          if (data._source_file?.last_modified || data._source_file?.last_modified_iso) {
            setLastResearchRun(data._source_file.last_modified_iso || new Date(data._source_file.last_modified * 1000).toISOString())
          }
        }
      } catch (err) {
        console.error('Failed to fetch brand research:', err)
      } finally {
        setIsLoadingResearch(false)
      }
    }

    fetchBrandResearch()
  }, [selectedBrandId])

  // Check if brand profile exists in campaigns directory
  const hasBrandProfile = selectedBrandId && brandIntelligence[selectedBrandId as keyof typeof brandIntelligence]

  // Helper to determine if we should show STORM Report hint
  const showStormReportHint = !brandResearch && brandReport

  return (
    <>
      <PageHeader
        title="Brand Intelligence"
        description="Comprehensive brand context and competitive landscape"
        showCampaignInfo={false}
      />

      {/* Brand Profile Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-foreground flex items-center justify-center">
              <Building2 className="h-5 w-5 text-background" />
            </div>
            {brandResearch?.brand || existingBrand?.name || selectedBrandId || 'Brand'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <span className="text-sm text-muted-foreground">Founded</span>
              <p className="font-mono font-medium text-lg">
                {brandResearch ? `Year ${brandResearch.founding_year}` : existingBrand?.foundingYear || (brandReport ? 'See STORM Report' : 'N/A')}
              </p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Headquarters</span>
              <p className="font-medium">{existingBrand?.headquarters || (brandReport ? 'See STORM Report' : 'N/A')}</p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Industry</span>
              <p className="font-medium">
                {brandResearch?.industry || existingBrand?.industry || (brandReport ? 'See STORM Report' : 'N/A')}
              </p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Size</span>
              <p className="font-medium">
                {brandResearch?.size || existingBrand?.size || (brandReport ? 'See STORM Report' : 'N/A')}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics Row */}
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Globe className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-3xl font-mono font-semibold">
                  {brandResearch ? brandResearch.primary_markets.length : existingBrand?.markets.length || (brandReport ? 0 : 0)}
                </p>
                <p className="text-sm text-muted-foreground">Active Markets</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Users className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-3xl font-mono font-semibold">
                  {brandResearch ? brandResearch.key_competitors.length : existingBrand?.competitors.length || (brandReport ? 0 : 0)}
                </p>
                <p className="text-sm text-muted-foreground">Key Competitors</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Building2 className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-3xl font-mono font-semibold">
                  {brandResearch ? brandResearch.sub_industries.length : existingBrand?.subIndustries.length || (brandReport ? 0 : 0)}
                </p>
                <p className="text-sm text-muted-foreground">Sub-Industries</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Historical Timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Historical Periods
            </CardTitle>
          </CardHeader>
          <CardContent>
            {showStormReportHint ? (
              <div className="py-8 text-center text-muted-foreground">
                <p>Historical data available in STORM Report</p>
                <p className="text-sm mt-2">View the full report for detailed historical context</p>
              </div>
            ) : (brandResearch?.historical_periods || existingBrand?.historicalPeriods || []).length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                No historical periods configured
              </div>
            ) : (
            <div className="relative">
              <div className="absolute left-2 top-0 bottom-0 w-0.5 bg-border" />
              <div className="space-y-4">
                {(brandResearch?.historical_periods || existingBrand?.historicalPeriods || []).map((period: any, i: number) => (
                  <div key={i} className="flex items-center gap-4 pl-6 relative">
                    <div className="absolute left-0 w-4 h-4 rounded-full bg-background border-2 border-foreground" />
                    <div>
                      <p className="font-mono text-sm text-muted-foreground">
                        {period.from_year || period.year} - {period.to_year || ''}
                      </p>
                      <p className="font-medium">{period.label}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            )}
          </CardContent>
        </Card>

        {/* Markets & Competitors */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Markets</CardTitle>
            </CardHeader>
            <CardContent>
              {showStormReportHint ? (
                <div className="py-4 text-center text-muted-foreground">
                  <p>Market data available in STORM Report</p>
                </div>
              ) : (brandResearch?.primary_markets || existingBrand?.markets || []).length === 0 ? (
                <div className="py-4 text-center text-muted-foreground">
                  No markets configured
                </div>
              ) : (
              <div className="flex flex-wrap gap-2">
                {(brandResearch?.primary_markets || existingBrand?.markets || []).map((market: any, i: number) => (
                  <Badge key={i} variant="secondary">
                    {typeof market === 'string' ? market : market.country}
                  </Badge>
                ))}
              </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Key Competitors</CardTitle>
            </CardHeader>
            <CardContent>
              {showStormReportHint ? (
                <div className="py-4 text-center text-muted-foreground">
                  <p>Competitor data available in STORM Report</p>
                </div>
              ) : (brandResearch?.key_competitors || existingBrand?.competitors || []).length === 0 ? (
                <div className="py-4 text-center text-muted-foreground">
                  No competitors configured
                </div>
              ) : (
              <div className="flex flex-wrap gap-2">
                {(brandResearch?.key_competitors || existingBrand?.competitors || []).map((competitor: string) => (
                  <Badge key={competitor} variant="outline">{competitor}</Badge>
                ))}
              </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Sub-Industries</CardTitle>
            </CardHeader>
            <CardContent>
              {showStormReportHint ? (
                <div className="py-4 text-center text-muted-foreground">
                  <p>Sub-industry data available in STORM Report</p>
                </div>
              ) : (brandResearch?.sub_industries || existingBrand?.subIndustries || []).length === 0 ? (
                <div className="py-4 text-center text-muted-foreground">
                  No sub-industries configured
                </div>
              ) : (
              <div className="flex flex-wrap gap-2">
                {(brandResearch?.sub_industries || existingBrand?.subIndustries || []).map((sub: string) => (
                  <Badge key={sub} variant="secondary">{sub}</Badge>
                ))}
              </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* STORM Report Section */}
      <div className="mt-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <RefreshCw className="h-4 w-4" />
                STORM Report
              </CardTitle>
              {brandReport && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsReportModalOpen(true)}
                  className="gap-2"
                >
                  <ExternalLink className="h-4 w-4" />
                  View Full STORM Report
                </Button>
              )}
            </div>
            {/* Last research run date */}
            {(lastResearchRun || (brandResearch?._source_file?.last_modified_iso)) && (
              <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                <Calendar className="h-3 w-3" />
                <span>
                  Last research run: {new Date(lastResearchRun || brandResearch!._source_file!.last_modified_iso!).toLocaleDateString()}
                </span>
              </div>
            )}
          </CardHeader>
          <CardContent>
            {isLoadingReport ? (
              <div className="py-8 text-center text-muted-foreground">
                Loading STORM Report...
              </div>
            ) : error ? (
              <div className="py-8 text-center text-red-500">
                {error}
              </div>
            ) : brandReport ? (
              <>
                <div className="mb-4 flex items-center gap-2 text-sm text-muted-foreground">
                  <span className="font-mono">Source:</span>
                  <span>{brandReport.filename}</span>
                </div>
                <MarkdownContent content={brandReport.content} />
              </>
            ) : showStormReportHint ? (
              <div className="py-8 text-center text-muted-foreground">
                <p>Brand intelligence data available in STORM Report</p>
                <p className="text-sm mt-2">View the full report for detailed brand context</p>
              </div>
            ) : (
              <div className="py-8 text-center text-muted-foreground">
                No STORM report available for this campaign
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Full STORM Report Modal */}
      {isReportModalOpen && brandReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col bg-background rounded-xl shadow-2xl">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <ExternalLink className="h-5 w-5" />
                Full STORM Report
              </h3>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsReportModalOpen(false)}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <MarkdownContent content={brandReport.content} />
            </div>
            <div className="p-4 border-t bg-muted/30">
              <Button
                variant="outline"
                onClick={() => setIsReportModalOpen(false)}
                className="w-full"
              >
                Close Report
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default function BrandIntelligencePage() {
  return (
    <DashboardLayout>
      <BrandIntelligenceContent />
    </DashboardLayout>
  )
}
