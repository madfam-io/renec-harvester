'use client'

import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LineChart, Line, PieChart, Pie, Cell } from 'recharts'
import { Activity, Clock, Database, AlertCircle } from 'lucide-react'

export default function MonitoringDashboard() {
  const [stats, setStats] = useState({
    totalRequests: 0,
    successfulRequests: 0,
    failedRequests: 0,
    itemsScraped: 0,
    currentSpeed: 0,
    avgResponseTime: 0,
    queueSize: 0,
    uptime: '00:00:00'
  })

  const [recentActivity, setRecentActivity] = useState([
    { time: '14:30', requests: 45, items: 12, errors: 2 },
    { time: '14:35', requests: 52, items: 15, errors: 1 },
    { time: '14:40', requests: 38, items: 10, errors: 3 },
    { time: '14:45', requests: 61, items: 18, errors: 0 },
    { time: '14:50', requests: 47, items: 14, errors: 1 },
  ])

  const [componentStats] = useState([
    { name: 'EC Standards', scraped: 1250, total: 1500, color: '#3B82F6' },
    { name: 'Certificadores', scraped: 890, total: 1200, color: '#10B981' },
    { name: 'Centers', scraped: 450, total: 800, color: '#F59E0B' },
    { name: 'Courses', scraped: 2100, total: 3500, color: '#EF4444' },
    { name: 'Sectors', scraped: 75, total: 100, color: '#8B5CF6' },
  ])

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/harvester/stats')
        if (response.ok) {
          const data = await response.json()
          setStats(data)
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 5000) // Update every 5 seconds
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Requests</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalRequests.toLocaleString()}</p>
            </div>
            <Activity className="w-8 h-8 text-blue-600" />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Success: {stats.successfulRequests} | Failed: {stats.failedRequests}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Items Scraped</p>
              <p className="text-2xl font-bold text-gray-900">{stats.itemsScraped.toLocaleString()}</p>
            </div>
            <Database className="w-8 h-8 text-green-600" />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Current Speed: {stats.currentSpeed}/min
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Response</p>
              <p className="text-2xl font-bold text-gray-900">{stats.avgResponseTime}ms</p>
            </div>
            <Clock className="w-8 h-8 text-yellow-600" />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Queue Size: {stats.queueSize}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Uptime</p>
              <p className="text-2xl font-bold text-gray-900">{stats.uptime}</p>
            </div>
            <Clock className="w-8 h-8 text-purple-600" />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            System Status: Running
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <LineChart width={500} height={250} data={recentActivity}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="requests" stroke="#3B82F6" name="Requests" />
            <Line type="monotone" dataKey="items" stroke="#10B981" name="Items" />
            <Line type="monotone" dataKey="errors" stroke="#EF4444" name="Errors" />
          </LineChart>
        </div>

        {/* Component Progress */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Component Progress</h3>
          <div className="space-y-3">
            {componentStats.map((component) => {
              const percentage = (component.scraped / component.total) * 100
              return (
                <div key={component.name}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-700">{component.name}</span>
                    <span className="text-gray-500">
                      {component.scraped}/{component.total} ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all duration-300"
                      style={{
                        width: `${percentage}%`,
                        backgroundColor: component.color
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <Database className="w-6 h-6 text-green-600" />
            </div>
            <p className="text-sm font-medium text-gray-900">Database</p>
            <p className="text-xs text-green-600">Healthy</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <Activity className="w-6 h-6 text-green-600" />
            </div>
            <p className="text-sm font-medium text-gray-900">Redis Cache</p>
            <p className="text-xs text-green-600">Connected</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <AlertCircle className="w-6 h-6 text-yellow-600" />
            </div>
            <p className="text-sm font-medium text-gray-900">Memory Usage</p>
            <p className="text-xs text-yellow-600">75%</p>
          </div>
        </div>
      </div>
    </div>
  )
}