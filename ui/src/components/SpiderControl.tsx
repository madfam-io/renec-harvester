'use client'

import { useState } from 'react'
import { Play, Pause, RotateCcw, Activity } from 'lucide-react'

export default function SpiderControl() {
  const [isRunning, setIsRunning] = useState(false)
  const [status, setStatus] = useState('idle')

  const handleStart = () => {
    setIsRunning(true)
    setStatus('running')
  }

  const handleStop = () => {
    setIsRunning(false)
    setStatus('stopped')
  }

  const handleReset = () => {
    setIsRunning(false)
    setStatus('idle')
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Spider Control</h3>
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${
          isRunning ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        }`}>
          <Activity className="w-4 h-4" />
          <span className="capitalize">{status}</span>
        </div>
      </div>

      <div className="flex space-x-4">
        <button
          onClick={isRunning ? handleStop : handleStart}
          className={`flex items-center space-x-2 px-4 py-2 rounded-md font-medium transition-colors ${
            isRunning
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-green-600 hover:bg-green-700 text-white'
          }`}
        >
          {isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          <span>{isRunning ? 'Stop' : 'Start'} Spider</span>
        </button>
        
        <button
          onClick={handleReset}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md font-medium transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reset</span>
        </button>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Pages Crawled</span>
          <p className="text-lg font-semibold">1,234</p>
        </div>
        <div>
          <span className="text-gray-500">Success Rate</span>
          <p className="text-lg font-semibold">98.5%</p>
        </div>
        <div>
          <span className="text-gray-500">Runtime</span>
          <p className="text-lg font-semibold">45m 23s</p>
        </div>
      </div>
    </div>
  )
}