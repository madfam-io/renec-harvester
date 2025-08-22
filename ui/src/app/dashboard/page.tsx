'use client'

import React from 'react'
import DataStats from '../../components/DataStats'
import SpiderControl from '../../components/SpiderControl'
import EntityFinder from '../../components/EntityFinder'
import NetworkVisualization from '../../components/NetworkVisualization'
import { Database, Search, Network, Activity } from 'lucide-react'

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-2xl font-bold text-gray-900">RENEC Harvester Dashboard</h1>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">Sprint 2 - Enhanced UI</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="mb-8">
          <nav className="flex space-x-4" aria-label="Tabs">
            <a
              href="#overview"
              className="flex items-center gap-2 px-3 py-2 font-medium text-sm rounded-md bg-blue-100 text-blue-700"
            >
              <Database className="w-4 h-4" />
              Overview
            </a>
            <a
              href="#finder"
              className="flex items-center gap-2 px-3 py-2 font-medium text-sm rounded-md text-gray-500 hover:text-gray-700"
            >
              <Search className="w-4 h-4" />
              Entity Finder
            </a>
            <a
              href="#network"
              className="flex items-center gap-2 px-3 py-2 font-medium text-sm rounded-md text-gray-500 hover:text-gray-700"
            >
              <Network className="w-4 h-4" />
              Network View
            </a>
            <a
              href="#spider"
              className="flex items-center gap-2 px-3 py-2 font-medium text-sm rounded-md text-gray-500 hover:text-gray-700"
            >
              <Activity className="w-4 h-4" />
              Spider Control
            </a>
          </nav>
        </div>

        {/* Content Sections */}
        <div className="space-y-8">
          {/* Overview Section */}
          <section id="overview">
            <h2 className="text-xl font-semibold mb-4">Data Overview</h2>
            <DataStats />
          </section>

          {/* Entity Finder Section */}
          <section id="finder">
            <EntityFinder />
          </section>

          {/* Network Visualization Section */}
          <section id="network">
            <NetworkVisualization />
          </section>

          {/* Spider Control Section */}
          <section id="spider">
            <h2 className="text-xl font-semibold mb-4">Spider Control</h2>
            <SpiderControl />
          </section>
        </div>
      </main>
    </div>
  )
}