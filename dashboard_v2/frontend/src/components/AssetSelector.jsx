import React from 'react'

function AssetSelector({ assets, selectedAsset, onChange }) {
  if (assets.length === 0) {
    return (
      <div className="card mb-4">
        <p className="text-secondary text-center py-4">No assets available</p>
      </div>
    )
  }
  
  return (
    <div className="card mb-4">
      <label className="text-sm font-semibold text-secondary mb-2 block">
        Select Asset
      </label>
      <select
        value={selectedAsset}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-card border border-border rounded p-2 text-sm focus:outline-none focus:border-accent"
      >
        {assets.map((asset) => (
          <option key={asset} value={asset}>
            {asset}
          </option>
        ))}
      </select>
    </div>
  )
}

export default AssetSelector
