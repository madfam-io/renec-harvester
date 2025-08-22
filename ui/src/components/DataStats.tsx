'use client'

import { Database, TrendingUp, Clock, CheckCircle } from 'lucide-react'

export default function DataStats() {
  const stats = [
    { label: 'Total Records', value: '12,543', icon: Database, color: 'text-blue-600' },
    { label: 'Growth Rate', value: '+15%', icon: TrendingUp, color: 'text-green-600' },
    { label: 'Last Updated', value: '2 hours ago', icon: Clock, color: 'text-yellow-600' },
    { label: 'Success Rate', value: '98.5%', icon: CheckCircle, color: 'text-emerald-600' },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat) => {
        const Icon = stat.icon
        return (
          <div key={stat.label} className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
              <Icon className={`w-8 h-8 ${stat.color}`} />
            </div>
          </div>
        )
      })}
    </div>
  )
}