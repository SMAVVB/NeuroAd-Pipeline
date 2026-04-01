import React, { useState } from 'react'

function BrainAnatomyInfo({ collapsed = false }) {
  const [isCollapsed, setIsCollapsed] = useState(collapsed)

  const regions = [
    { name: 'TPJ', description: 'Temporoparietal Junction - Sozialer Kontext & Aufmerksamkeit', icon: '🌐' },
    { name: 'FFA', description: 'Fusiform Face Area - Gesichtserkennung', icon: '👤' },
    { name: 'PPA', description: 'Parahippocampal Place Area - Raumorientierung', icon: '📍' },
    { name: 'V5', description: 'MT/V5 - Bewegungswahrnehmung', icon: '⚡' },
    { name: 'Broca', description: 'Broca-Areal - Sprachverarbeitung', icon: '💬' },
    { name: 'A1', description: 'Primäres Auditives Kortex - Hören', icon: '👂' },
  ]

  return (
    <div className="card mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Gehirn-Anatomie — Was bedeuten die Regionen?</h3>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-sm text-accent hover:text-accent-hover"
        >
          {isCollapsed ? '▼ Erweitern' : '▲ Verstecken'}
        </button>
      </div>

      {!isCollapsed && (
        <div className="flex flex-col md:flex-row gap-6">
          {/* SVG Brain Silhouette */}
          <div className="flex-1 relative h-64">
            <svg viewBox="0 0 400 200" className="w-full h-full">
              {/* Brain silhouette */}
              <path
                d="M100,100 Q120,60 150,50 Q200,40 250,50 Q280,60 300,100 Q320,140 300,180 Q200,190 100,180 Q80,140 100,100 Z"
                fill="none"
                stroke="var(--text-secondary)"
                strokeWidth="2"
              />
              
              {/* ROI markers */}
              {regions.map((region, i) => {
                const positions = [
                  { cx: 280, cy: 80 },  // TPJ - rechts hinten oben
                  { cx: 260, cy: 120 }, // FFA - rechts unten mitte
                  { cx: 140, cy: 80 },  // PPA - links hinten
                  { cx: 270, cy: 60 },  // V5 - rechts hinten
                  { cx: 160, cy: 100 }, // Broca - links vorne
                  { cx: 290, cy: 100 }, // A1 - rechts seite
                ]
                const pos = positions[i]
                
                return (
                  <g key={region.name}>
                    <circle
                      cx={pos.cx}
                      cy={pos.cy}
                      r="4"
                      fill="#dc2626"
                      stroke="var(--bg-card)"
                      strokeWidth="1"
                    />
                    <line
                      x1={pos.cx + 10}
                      y1={pos.cy}
                      x2={pos.cx + 30}
                      y2={pos.cy}
                      stroke="var(--text-secondary)"
                      strokeWidth="1"
                      strokeDasharray="2,2"
                    />
                  </g>
                )
              })}
            </svg>
          </div>

          {/* Info boxes */}
          <div className="flex-1 grid grid-cols-2 gap-3">
            {regions.map((region) => (
              <div key={region.name} className="bg-subtle rounded p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{region.icon}</span>
                  <span className="font-semibold text-sm">{region.name}</span>
                </div>
                <p className="text-xs text-secondary">{region.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default BrainAnatomyInfo
