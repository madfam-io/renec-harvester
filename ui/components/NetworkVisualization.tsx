'use client'

import React, { useEffect, useRef, useState } from 'react'
import { Network, Share2, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import axios from 'axios'

interface Node {
  id: string
  type: string
  label: string
  properties: Record<string, any>
}

interface Edge {
  id: string
  source: string
  target: string
  type: string
  properties?: Record<string, any>
}

interface GraphData {
  nodes: Node[]
  edges: Edge[]
}

export default function NetworkVisualization() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [zoom, setZoom] = useState(1)

  // Load sample graph data
  const loadGraphData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // In a real implementation, this would fetch from the graph export endpoint
      const sampleData: GraphData = {
        nodes: [
          { id: 'ec_EC0217', type: 'ec_standard', label: 'EC0217', properties: { titulo: 'Impartición de cursos', vigente: true } },
          { id: 'cert_ECE001-99', type: 'certificador', label: 'ECE001-99', properties: { nombre: 'CONOCER', tipo: 'ECE' } },
          { id: 'cert_ECE002-99', type: 'certificador', label: 'ECE002-99', properties: { nombre: 'CENEVAL', tipo: 'ECE' } },
          { id: 'centro_CE0001', type: 'centro', label: 'CE0001', properties: { nombre: 'Centro de Evaluación CDMX' } },
          { id: 'sector_1', type: 'sector', label: 'Sector 1', properties: { nombre: 'Educación' } }
        ],
        edges: [
          { id: 'rel_1', source: 'cert_ECE001-99', target: 'ec_EC0217', type: 'accredits' },
          { id: 'rel_2', source: 'cert_ECE002-99', target: 'ec_EC0217', type: 'accredits' },
          { id: 'rel_3', source: 'centro_CE0001', target: 'ec_EC0217', type: 'evaluates' },
          { id: 'rel_4', source: 'ec_EC0217', target: 'sector_1', type: 'belongs_to' }
        ]
      }
      
      setGraphData(sampleData)
      
      // Draw the network
      if (canvasRef.current) {
        drawNetwork(sampleData)
      }
    } catch (err) {
      setError('Failed to load network data')
      console.error('Network load error:', err)
    } finally {
      setLoading(false)
    }
  }

  const drawNetwork = (data: GraphData) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Calculate node positions (simple circular layout)
    const centerX = canvas.width / 2
    const centerY = canvas.height / 2
    const radius = Math.min(canvas.width, canvas.height) * 0.3

    const nodePositions: Record<string, { x: number; y: number }> = {}
    
    data.nodes.forEach((node, index) => {
      const angle = (index / data.nodes.length) * 2 * Math.PI
      nodePositions[node.id] = {
        x: centerX + radius * Math.cos(angle) * zoom,
        y: centerY + radius * Math.sin(angle) * zoom
      }
    })

    // Draw edges
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 2
    data.edges.forEach(edge => {
      const source = nodePositions[edge.source]
      const target = nodePositions[edge.target]
      if (source && target) {
        ctx.beginPath()
        ctx.moveTo(source.x, source.y)
        ctx.lineTo(target.x, target.y)
        ctx.stroke()
      }
    })

    // Draw nodes
    data.nodes.forEach(node => {
      const pos = nodePositions[node.id]
      if (!pos) return

      // Node color based on type
      const colors = {
        ec_standard: '#3b82f6',
        certificador: '#10b981',
        centro: '#f97316',
        sector: '#8b5cf6'
      }
      
      ctx.fillStyle = colors[node.type as keyof typeof colors] || '#6b7280'
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, 20 * zoom, 0, 2 * Math.PI)
      ctx.fill()
      
      // Node label
      ctx.fillStyle = '#ffffff'
      ctx.font = `${12 * zoom}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(node.label, pos.x, pos.y)
      
      // Node type label
      ctx.fillStyle = '#4b5563'
      ctx.font = `${10 * zoom}px sans-serif`
      ctx.fillText(node.type, pos.x, pos.y + 30 * zoom)
    })
  }

  useEffect(() => {
    loadGraphData()
  }, [])

  useEffect(() => {
    if (graphData && canvasRef.current) {
      drawNetwork(graphData)
    }
  }, [graphData, zoom])

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.1, 2))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.1, 0.5))
  const handleReset = () => setZoom(1)

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Network className="w-6 h-6" />
          Entity Network
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Zoom out"
          >
            <ZoomOut className="w-5 h-5" />
          </button>
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Zoom in"
          >
            <ZoomIn className="w-5 h-5" />
          </button>
          <button
            onClick={handleReset}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Reset view"
          >
            <Maximize2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Canvas container */}
      <div className="relative bg-gray-50 rounded-lg overflow-hidden" style={{ height: '500px' }}>
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <p className="text-gray-500 mt-2">Loading network...</p>
            </div>
          </div>
        )}
        
        {error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <Share2 className="w-12 h-12 text-gray-300 mx-auto mb-2" />
              <p className="text-gray-500">{error}</p>
            </div>
          </div>
        )}

        <canvas
          ref={canvasRef}
          className="w-full h-full cursor-move"
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
          <span>EC Standards</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded-full"></div>
          <span>Certificadores</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-orange-500 rounded-full"></div>
          <span>Centros</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-purple-500 rounded-full"></div>
          <span>Sectores</span>
        </div>
      </div>

      {/* Selected node details */}
      {selectedNode && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold mb-2">{selectedNode.label}</h3>
          <div className="text-sm text-gray-600">
            <p>Type: {selectedNode.type}</p>
            {Object.entries(selectedNode.properties).map(([key, value]) => (
              <p key={key}>{key}: {value?.toString()}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}