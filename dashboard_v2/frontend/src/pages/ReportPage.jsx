import React, { useState, useEffect } from 'react'
import InfoBlock from '../components/InfoBlock.jsx'
import ScoreCard from '../components/ScoreCard.jsx'

function ReportPage({ campaign }) {
  const [report, setReport] = useState('')
  const [loading, setLoading] = useState(false)
  const [focus, setFocus] = useState('full')
  const [showReport, setShowReport] = useState(false)

  const generateReport = async () => {
    try {
      setLoading(true)
      setReport('')
      setShowReport(true)

      // Fetch report from API
      const response = await fetch(`/api/report/generate?campaign=${encodeURIComponent(campaign)}&focus=${focus}`)
      const data = await response.json()

      if (data.status === 'success') {
        // Simulate streaming effect
        const text = data.report
        let currentText = ''
        const words = text.split(' ')
        
        for (let i = 0; i < words.length; i++) {
          currentText += (i > 0 ? ' ' : '') + words[i]
          setReport(currentText)
          await new Promise(resolve => setTimeout(resolve, 15))
        }
      }
    } catch (err) {
      console.error('Failed to generate report:', err)
      setReport('Fehler beim Generieren des Reports.')
    } finally {
      setLoading(false)
    }
  }

  const copyReport = () => {
    navigator.clipboard.writeText(report)
    alert('Report in die Zwischenablage kopiert!')
  }

  const renderMarkdown = (text) => {
    // Simple markdown rendering
    const lines = text.split('\n')
    return lines.map((line, index) => {
      // Check for bold text
      const parts = line.split(/(\*\*.*?\*\*)/g)
      
      if (line.startsWith('# ')) {
        return (
          <h2 key={index} style={{ fontSize: '18px', fontWeight: 600, margin: '20px 0 8px' }}>
            {renderInlineMarkdown(line.substring(2))}
          </h2>
        )
      }
      if (line.startsWith('## ')) {
        return (
          <h3 key={index} style={{ fontSize: '15px', fontWeight: 600, margin: '16px 0 6px' }}>
            {renderInlineMarkdown(line.substring(3))}
          </h3>
        )
      }
      if (/^\d+\.\s/.test(line)) {
        return (
          <div key={index} style={{ margin: '4px 0', paddingLeft: '20px' }}>
            <span style={{ fontWeight: 600 }}>{line.split('.')[0]}.</span>{' '}
            {renderInlineMarkdown(line.split('.').slice(1).join('.'))}
          </div>
        )
      }
      
      return (
        <p key={index} style={{ margin: '8px 0' }}>
          {renderInlineMarkdown(line)}
        </p>
      )
    })
  }

  const renderInlineMarkdown = (text) => {
    const parts = text.split(/(\*\*.*?\*\*)/g)
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index}>{part.substring(2, part.length - 2)}</strong>
      }
      return part
    })
  }

  return (
    <div className="space-y-6">
      {/* Info Block */}
      <InfoBlock
        title="Report & Insights"
        description="KI-generierte Analyse aller Pipeline-Ergebnisse. Die KI wertet alle Scoring-Daten aus und gibt actionable Empfehlungen für Marketing-Entscheider — ohne Neuromarketing-Vorkenntnisse."
        example="Der Report analysiert alle Campaign-Daten und gibt konkrete Handlungsempfehlungen für die Optimierung der Werbekampagne."
      />

      {/* Generate Report Section */}
      <div className="card">
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={generateReport}
              disabled={loading}
              className="btn-primary"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin">⏳</span>
                  Analyse läuft...
                </span>
              ) : (
                'Report generieren'
              )}
            </button>

            <button
              onClick={copyReport}
              disabled={!showReport || loading}
              className="btn-secondary"
            >
              📋 Report kopieren
            </button>

            <select
              value={focus}
              onChange={(e) => setFocus(e.target.value)}
              className="bg-card border border-border rounded p-2 text-sm focus:outline-none focus:border-accent"
            >
              <option value="full">Vollständige Analyse</option>
              <option value="optimization">Optimierungsempfehlungen</option>
              <option value="executive">Executive Summary (1 Seite)</option>
            </select>
          </div>

          <div className="text-xs text-secondary">
            Powered by Lemonade SDK · localhost:8888
          </div>
        </div>
      </div>

      {/* Report Card */}
      {showReport && (
        <div className="card" style={{ padding: '28px', backgroundColor: '#ffffff' }}>
          {report ? (
            <div className="prose dark:prose-invert max-w-none">
              {renderMarkdown(report)}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-secondary">Klicke auf 'Report generieren' um eine KI-Analyse aller Kampagnendaten zu erstellen.</p>
            </div>
          )}
        </div>
      )}

      {/* Summary Table */}
      {showReport && report && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Alle Creatives im Überblick</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-secondary uppercase bg-subtle">
                <tr>
                  <th className="px-4 py-3">Asset</th>
                  <th className="px-4 py-3">Neural Engagement</th>
                  <th className="px-4 py-3">Brand Match</th>
                  <th className="px-4 py-3">Emotion Valence</th>
                  <th className="px-4 py-3">Center Bias</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border">
                  <td className="px-4 py-3 font-medium">{campaign}</td>
                  <td className="px-4 py-3">0.75</td>
                  <td className="px-4 py-3">0.42</td>
                  <td className="px-4 py-3">0.38</td>
                  <td className="px-4 py-3">0.62</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReportPage
