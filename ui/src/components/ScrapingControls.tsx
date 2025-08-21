'use client'

import { useState } from 'react'
import { Play, Pause, RotateCcw, Settings2, Save } from 'lucide-react'

interface ScrapingControlsProps {
  isActive: boolean
  onToggle: (active: boolean) => void
}

export default function ScrapingControls({ isActive, onToggle }: ScrapingControlsProps) {
  const [settings, setSettings] = useState({
    mode: 'crawl',
    maxDepth: 5,
    concurrentRequests: 8,
    downloadDelay: 0.5,
    retryTimes: 3,
    respectRobotsTxt: true,
    enableCaching: true,
    targetComponents: {
      'ec_standards': true,
      'certificadores': true,
      'evaluation_centers': true,
      'courses': true,
      'sectors': true,
      'committees': false,
    }
  })

  const handleStart = async () => {
    try {
      const response = await fetch('/api/harvester/spider/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      })
      if (response.ok) {
        onToggle(true)
      }
    } catch (error) {
      console.error('Failed to start scraping:', error)
    }
  }

  const handleStop = async () => {
    try {
      const response = await fetch('/api/harvester/spider/stop', {
        method: 'POST'
      })
      if (response.ok) {
        onToggle(false)
      }
    } catch (error) {
      console.error('Failed to stop scraping:', error)
    }
  }

  const handleReset = async () => {
    try {
      await fetch('/api/harvester/spider/reset', { method: 'POST' })
    } catch (error) {
      console.error('Failed to reset scraping:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Control Buttons */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Scraping Controls</h2>
        <div className="flex space-x-4">
          <button
            onClick={isActive ? handleStop : handleStart}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md font-medium ${
              isActive
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            {isActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            <span>{isActive ? 'Stop' : 'Start'} Scraping</span>
          </button>
          
          <button
            onClick={handleReset}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md font-medium"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Configuration</h2>
          <button
            className="flex items-center space-x-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium"
          >
            <Save className="w-4 h-4" />
            <span>Save</span>
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Basic Settings */}
          <div className="space-y-4">
            <h3 className="text-md font-medium text-gray-800">Basic Settings</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Scraping Mode
              </label>
              <select
                value={settings.mode}
                onChange={(e) => setSettings(prev => ({ ...prev, mode: e.target.value }))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="crawl">Crawl (Discovery)</option>
                <option value="harvest">Harvest (Data Extraction)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Crawl Depth
              </label>
              <input
                type="number"
                value={settings.maxDepth}
                onChange={(e) => setSettings(prev => ({ ...prev, maxDepth: parseInt(e.target.value) }))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="10"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Concurrent Requests
              </label>
              <input
                type="number"
                value={settings.concurrentRequests}
                onChange={(e) => setSettings(prev => ({ ...prev, concurrentRequests: parseInt(e.target.value) }))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="20"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Download Delay (seconds)
              </label>
              <input
                type="number"
                step="0.1"
                value={settings.downloadDelay}
                onChange={(e) => setSettings(prev => ({ ...prev, downloadDelay: parseFloat(e.target.value) }))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="0"
                max="5"
              />
            </div>
          </div>

          {/* Target Components */}
          <div className="space-y-4">
            <h3 className="text-md font-medium text-gray-800">Target Components</h3>
            
            {Object.entries(settings.targetComponents).map(([component, enabled]) => (
              <label key={component} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    targetComponents: {
                      ...prev.targetComponents,
                      [component]: e.target.checked
                    }
                  }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 capitalize">
                  {component.replace('_', ' ')}
                </span>
              </label>
            ))}

            <div className="space-y-2 mt-6">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.respectRobotsTxt}
                  onChange={(e) => setSettings(prev => ({ ...prev, respectRobotsTxt: e.target.checked }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Respect robots.txt</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.enableCaching}
                  onChange={(e) => setSettings(prev => ({ ...prev, enableCaching: e.target.checked }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Enable caching</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}