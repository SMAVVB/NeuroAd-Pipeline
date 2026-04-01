import React from 'react'

function InfoBlock({ title, description, example }) {
  return (
    <div className="card mb-8">
      <div className="flex items-start gap-4">
        <div className="flex-1">
          <h2 className="text-xl font-bold mb-2">{title}</h2>
          <p className="text-secondary mb-4">{description}</p>
          {example && (
            <div className="bg-accent/5 border border-accent/20 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-accent font-semibold">💡 Example</span>
              </div>
              <p className="text-sm text-secondary">{example}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default InfoBlock
