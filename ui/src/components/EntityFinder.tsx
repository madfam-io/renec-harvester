'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { Search, Filter, ChevronRight, Building, Award, MapPin, Briefcase } from 'lucide-react'
import axios from 'axios'
import { useRouter } from 'next/navigation'
import { useDebounce } from '../hooks/useDebounce'

interface SearchResult {
  ec_standards?: {
    count: number
    items: Array<{
      ec_clave: string
      titulo: string
      vigente: boolean
      sector: string
      nivel: string
    }>
  }
  certificadores?: {
    count: number
    items: Array<{
      cert_id: string
      tipo: string
      nombre_legal: string
      siglas?: string
      estado: string
      estatus: string
    }>
  }
  centros?: {
    count: number
    items: Array<{
      centro_id: string
      nombre: string
      estado: string
      municipio: string
    }>
  }
  sectores?: {
    count: number
    items: Array<{
      sector_id: number
      nombre: string
    }>
  }
  comites?: {
    count: number
    items: Array<{
      comite_id: number
      nombre: string
      sector_id?: number
    }>
  }
}

export default function EntityFinder() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['ec_standards', 'certificadores', 'centros'])
  const [results, setResults] = useState<SearchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const debouncedQuery = useDebounce(searchQuery, 300)

  const entityTypes = [
    { id: 'ec_standards', label: 'EC Standards', icon: Award },
    { id: 'certificadores', label: 'Certificadores', icon: Building },
    { id: 'centros', label: 'Centros', icon: MapPin },
    { id: 'sectores', label: 'Sectores', icon: Briefcase },
    { id: 'comites', label: 'Comités', icon: Briefcase }
  ]

  const search = useCallback(async (query: string) => {
    if (!query || query.length < 2) {
      setResults(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.get('/api/v1/search', {
        params: {
          q: query,
          entity_types: selectedTypes.join(','),
          limit: 10
        }
      })
      setResults(response.data.results)
    } catch (err) {
      setError('Error searching entities')
      console.error('Search error:', err)
    } finally {
      setLoading(false)
    }
  }, [selectedTypes])

  useEffect(() => {
    search(debouncedQuery)
  }, [debouncedQuery, search])

  const toggleEntityType = (type: string) => {
    setSelectedTypes(prev =>
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    )
  }

  const getEntityIcon = (type: string) => {
    const entity = entityTypes.find(e => e.id === type)
    return entity?.icon || ChevronRight
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-2xl font-bold mb-6">Entity Finder</h2>

      {/* Search Input */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search EC standards, certificadores, centers..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Entity Type Filters */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600">Filter by type:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {entityTypes.map(type => {
            const Icon = type.icon
            const isSelected = selectedTypes.includes(type.id)
            return (
              <button
                key={type.id}
                onClick={() => toggleEntityType(type.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-colors ${
                  isSelected
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Icon className="w-4 h-4" />
                {type.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="text-gray-500 mt-2">Searching...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Results */}
      {results && !loading && (
        <div className="space-y-6">
          {/* EC Standards */}
          {results.ec_standards && results.ec_standards.count > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Award className="w-5 h-5 text-blue-500" />
                EC Standards ({results.ec_standards.count})
              </h3>
              <div className="space-y-2">
                {results.ec_standards.items.map(item => (
                  <div
                    key={item.ec_clave}
                    className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
                    onClick={() => router.push(`/entity/ec-standard/${item.ec_clave}`)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-blue-600">{item.ec_clave}</h4>
                        <p className="text-gray-700 mt-1">{item.titulo}</p>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                          <span>Sector: {item.sector}</span>
                          <span>Nivel: {item.nivel}</span>
                          <span className={`px-2 py-0.5 rounded-full text-xs ${
                            item.vigente ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                          }`}>
                            {item.vigente ? 'Vigente' : 'No vigente'}
                          </span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400 mt-1" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Certificadores */}
          {results.certificadores && results.certificadores.count > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Building className="w-5 h-5 text-green-500" />
                Certificadores ({results.certificadores.count})
              </h3>
              <div className="space-y-2">
                {results.certificadores.items.map(item => (
                  <div
                    key={item.cert_id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-green-300 transition-colors cursor-pointer"
                    onClick={() => router.push(`/entity/certificador/${item.cert_id}`)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-green-600">{item.cert_id}</h4>
                        <p className="text-gray-700 mt-1">{item.nombre_legal}</p>
                        {item.siglas && (
                          <p className="text-gray-500 text-sm">({item.siglas})</p>
                        )}
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                          <span className={`px-2 py-0.5 rounded ${
                            item.tipo === 'ECE' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                          }`}>
                            {item.tipo}
                          </span>
                          <span>{item.estado}</span>
                          <span className={`px-2 py-0.5 rounded-full text-xs ${
                            item.estatus === 'Vigente' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {item.estatus}
                          </span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400 mt-1" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Centros */}
          {results.centros && results.centros.count > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-orange-500" />
                Centros de Evaluación ({results.centros.count})
              </h3>
              <div className="space-y-2">
                {results.centros.items.map(item => (
                  <div
                    key={item.centro_id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-orange-300 transition-colors cursor-pointer"
                    onClick={() => router.push(`/entity/centro/${item.centro_id}`)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-orange-600">{item.centro_id}</h4>
                        <p className="text-gray-700 mt-1">{item.nombre}</p>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                          <span>{item.estado}</span>
                          <span>{item.municipio}</span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400 mt-1" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sectores */}
          {results.sectores && results.sectores.count > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-purple-500" />
                Sectores ({results.sectores.count})
              </h3>
              <div className="space-y-2">
                {results.sectores.items.map(item => (
                  <div
                    key={item.sector_id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-purple-300 transition-colors cursor-pointer"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-purple-600">Sector {item.sector_id}</h4>
                        <p className="text-gray-700 mt-1">{item.nombre}</p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400 mt-1" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No results */}
          {Object.keys(results).length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No results found for "{searchQuery}"
            </div>
          )}
        </div>
      )}
    </div>
  )
}