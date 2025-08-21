'use client'

import { useState, useEffect } from 'react'
import { Play, Pause, Settings, Database, Activity, Download } from 'lucide-react'
import ScrapingControls from '@/components/ScrapingControls'
import MonitoringDashboard from '@/components/MonitoringDashboard'
import DataExplorer from '@/components/DataExplorer'

export default function Home() {
  const [activeTab, setActiveTab] = useState('controls')
  const [isScrapingActive, setIsScrapingActive] = useState(false)

  const tabs = [
    { id: 'controls', label: 'Scraping Controls', icon: Settings },
    { id: 'monitor', label: 'Monitoring', icon: Activity },
    { id: 'data', label: 'Data Explorer', icon: Database },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">RENEC Harvester</h1>
            <p className="text-sm text-gray-600">México RENEC Platform Data Harvester</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${
              isScrapingActive 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                isScrapingActive ? 'bg-green-500' : 'bg-gray-400'
              }`} />
              {isScrapingActive ? 'Active' : 'Idle'}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="px-6">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="px-6 py-8">
        {activeTab === 'controls' && (
          <ScrapingControls 
            isActive={isScrapingActive}
            onToggle={setIsScrapingActive}
          />
        )}
        {activeTab === 'monitor' && <MonitoringDashboard />}
        {activeTab === 'data' && <DataExplorer />}
      </main>
    </div>
  )
}