'use client'

import React, { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import axios from 'axios'
import { ArrowLeft, Award, Building, MapPin, Briefcase, Calendar, Globe, Phone, Mail, User } from 'lucide-react'

interface EntityDetail {
  // EC Standard
  ec_clave?: string
  titulo?: string
  version?: string
  vigente?: boolean
  sector?: string
  comite?: string
  descripcion?: string
  competencias?: string[]
  nivel?: string
  duracion_horas?: number
  fecha_publicacion?: string
  fecha_vigencia?: string
  certificadores?: any[]
  
  // Certificador
  cert_id?: string
  tipo?: string
  nombre_legal?: string
  siglas?: string
  estatus?: string
  domicilio_texto?: string
  estado?: string
  municipio?: string
  telefono?: string
  correo?: string
  sitio_web?: string
  representante_legal?: string
  ec_standards?: any[]
  
  // Centro
  centro_id?: string
  nombre?: string
  coordinador?: string
  
  // Common
  first_seen?: string
  last_seen?: string
}

export default function EntityDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [entity, setEntity] = useState<EntityDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchEntity = async () => {
      if (!params.type || !params.id) return

      setLoading(true)
      setError(null)

      try {
        let endpoint = ''
        const entityType = params.type as string
        const entityId = params.id as string

        switch (entityType) {
          case 'ec-standard':
            endpoint = `/api/v1/ec-standards/${entityId}`
            break
          case 'certificador':
            endpoint = `/api/v1/certificadores/${entityId}`
            break
          case 'centro':
            endpoint = `/api/v1/centros/${entityId}`
            break
          default:
            throw new Error('Invalid entity type')
        }

        const response = await axios.get(endpoint)
        setEntity(response.data)
      } catch (err) {
        setError('Failed to load entity details')
        console.error('Entity fetch error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchEntity()
  }, [params])

  const getEntityIcon = () => {
    switch (params.type) {
      case 'ec-standard':
        return Award
      case 'certificador':
        return Building
      case 'centro':
        return MapPin
      default:
        return Briefcase
    }
  }

  const EntityIcon = getEntityIcon()

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="text-gray-500 mt-2">Loading entity details...</p>
        </div>
      </div>
    )
  }

  if (error || !entity) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Entity not found'}</p>
          <button
            onClick={() => router.back()}
            className="text-blue-600 hover:text-blue-800"
          >
            Go back
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 h-16">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <EntityIcon className="w-6 h-6 text-gray-600" />
              <h1 className="text-xl font-bold text-gray-900">
                {entity.ec_clave || entity.cert_id || entity.centro_id || 'Entity Details'}
              </h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm p-6">
          {/* EC Standard Details */}
          {params.type === 'ec-standard' && (
            <>
              <div className="mb-6">
                <h2 className="text-2xl font-bold mb-2">{entity.titulo}</h2>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <span className={`px-3 py-1 rounded-full ${
                    entity.vigente ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {entity.vigente ? 'Vigente' : 'No vigente'}
                  </span>
                  <span>Version: {entity.version || 'N/A'}</span>
                  <span>Nivel: {entity.nivel || 'N/A'}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold mb-3">General Information</h3>
                  <dl className="space-y-2">
                    <div>
                      <dt className="text-sm text-gray-500">Sector</dt>
                      <dd className="text-gray-900">{entity.sector || 'N/A'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">Comité</dt>
                      <dd className="text-gray-900">{entity.comite || 'N/A'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">Duration</dt>
                      <dd className="text-gray-900">{entity.duracion_horas ? `${entity.duracion_horas} hours` : 'N/A'}</dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h3 className="font-semibold mb-3">Dates</h3>
                  <dl className="space-y-2">
                    <div>
                      <dt className="text-sm text-gray-500">Publication Date</dt>
                      <dd className="text-gray-900">
                        {entity.fecha_publicacion ? new Date(entity.fecha_publicacion).toLocaleDateString() : 'N/A'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">Validity Date</dt>
                      <dd className="text-gray-900">
                        {entity.fecha_vigencia ? new Date(entity.fecha_vigencia).toLocaleDateString() : 'N/A'}
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>

              {entity.descripcion && (
                <div className="mt-6">
                  <h3 className="font-semibold mb-3">Description</h3>
                  <p className="text-gray-700 whitespace-pre-line">{entity.descripcion}</p>
                </div>
              )}

              {entity.competencias && entity.competencias.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-semibold mb-3">Competencies</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {entity.competencias.map((comp, idx) => (
                      <li key={idx} className="text-gray-700">{comp}</li>
                    ))}
                  </ul>
                </div>
              )}

              {entity.certificadores && entity.certificadores.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-semibold mb-3">Accredited Certificadores</h3>
                  <div className="space-y-2">
                    {entity.certificadores.map((cert: any) => (
                      <div key={cert.cert_id} className="border rounded-lg p-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{cert.cert_id}</p>
                            <p className="text-sm text-gray-600">{cert.nombre_legal}</p>
                          </div>
                          <span className={`px-2 py-1 text-xs rounded ${
                            cert.tipo === 'ECE' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                          }`}>
                            {cert.tipo}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Certificador Details */}
          {params.type === 'certificador' && (
            <>
              <div className="mb-6">
                <h2 className="text-2xl font-bold mb-2">{entity.nombre_legal}</h2>
                <div className="flex items-center gap-4 text-sm">
                  <span className={`px-3 py-1 rounded ${
                    entity.tipo === 'ECE' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                  }`}>
                    {entity.tipo}
                  </span>
                  <span className={`px-3 py-1 rounded-full ${
                    entity.estatus === 'Vigente' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {entity.estatus}
                  </span>
                  {entity.siglas && <span className="text-gray-600">({entity.siglas})</span>}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold mb-3">Contact Information</h3>
                  <dl className="space-y-3">
                    {entity.telefono && (
                      <div className="flex items-start gap-2">
                        <Phone className="w-4 h-4 text-gray-400 mt-0.5" />
                        <div>
                          <dt className="text-sm text-gray-500">Phone</dt>
                          <dd className="text-gray-900">{entity.telefono}</dd>
                        </div>
                      </div>
                    )}
                    {entity.correo && (
                      <div className="flex items-start gap-2">
                        <Mail className="w-4 h-4 text-gray-400 mt-0.5" />
                        <div>
                          <dt className="text-sm text-gray-500">Email</dt>
                          <dd className="text-gray-900">{entity.correo}</dd>
                        </div>
                      </div>
                    )}
                    {entity.sitio_web && (
                      <div className="flex items-start gap-2">
                        <Globe className="w-4 h-4 text-gray-400 mt-0.5" />
                        <div>
                          <dt className="text-sm text-gray-500">Website</dt>
                          <dd className="text-gray-900">
                            <a href={entity.sitio_web} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                              {entity.sitio_web}
                            </a>
                          </dd>
                        </div>
                      </div>
                    )}
                  </dl>
                </div>

                <div>
                  <h3 className="font-semibold mb-3">Location</h3>
                  <dl className="space-y-2">
                    <div>
                      <dt className="text-sm text-gray-500">Address</dt>
                      <dd className="text-gray-900">{entity.domicilio_texto || 'N/A'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">State</dt>
                      <dd className="text-gray-900">{entity.estado || 'N/A'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">Municipality</dt>
                      <dd className="text-gray-900">{entity.municipio || 'N/A'}</dd>
                    </div>
                  </dl>
                </div>
              </div>

              {entity.representante_legal && (
                <div className="mt-6">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <User className="w-4 h-4" />
                    Legal Representative
                  </h3>
                  <p className="text-gray-700">{entity.representante_legal}</p>
                </div>
              )}

              {entity.ec_standards && entity.ec_standards.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-semibold mb-3">Accredited EC Standards</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {entity.ec_standards.map((ec: any) => (
                      <div key={ec.ec_clave} className="border rounded-lg p-3">
                        <p className="font-medium text-blue-600">{ec.ec_clave}</p>
                        <p className="text-sm text-gray-600">{ec.titulo}</p>
                        <span className={`text-xs ${
                          ec.vigente ? 'text-green-600' : 'text-gray-500'
                        }`}>
                          {ec.vigente ? 'Vigente' : 'No vigente'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Centro Details */}
          {params.type === 'centro' && (
            <>
              <div className="mb-6">
                <h2 className="text-2xl font-bold mb-2">{entity.nombre}</h2>
                <p className="text-gray-600">{entity.centro_id}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold mb-3">Contact Information</h3>
                  <dl className="space-y-3">
                    {entity.coordinador && (
                      <div className="flex items-start gap-2">
                        <User className="w-4 h-4 text-gray-400 mt-0.5" />
                        <div>
                          <dt className="text-sm text-gray-500">Coordinator</dt>
                          <dd className="text-gray-900">{entity.coordinador}</dd>
                        </div>
                      </div>
                    )}
                    {entity.telefono && (
                      <div className="flex items-start gap-2">
                        <Phone className="w-4 h-4 text-gray-400 mt-0.5" />
                        <div>
                          <dt className="text-sm text-gray-500">Phone</dt>
                          <dd className="text-gray-900">{entity.telefono}</dd>
                        </div>
                      </div>
                    )}
                    {entity.correo && (
                      <div className="flex items-start gap-2">
                        <Mail className="w-4 h-4 text-gray-400 mt-0.5" />
                        <div>
                          <dt className="text-sm text-gray-500">Email</dt>
                          <dd className="text-gray-900">{entity.correo}</dd>
                        </div>
                      </div>
                    )}
                  </dl>
                </div>

                <div>
                  <h3 className="font-semibold mb-3">Location</h3>
                  <dl className="space-y-2">
                    <div>
                      <dt className="text-sm text-gray-500">State</dt>
                      <dd className="text-gray-900">{entity.estado || 'N/A'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">Municipality</dt>
                      <dd className="text-gray-900">{entity.municipio || 'N/A'}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            </>
          )}

          {/* Metadata */}
          <div className="mt-8 pt-6 border-t">
            <h3 className="font-semibold mb-3 text-sm text-gray-600">Metadata</h3>
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-gray-500">First Seen</dt>
                <dd className="text-gray-700">
                  {entity.first_seen ? new Date(entity.first_seen).toLocaleString() : 'N/A'}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Last Updated</dt>
                <dd className="text-gray-700">
                  {entity.last_seen ? new Date(entity.last_seen).toLocaleString() : 'N/A'}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </main>
    </div>
  )
}