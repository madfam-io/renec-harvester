'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ChevronRight, Sparkles, Database, Download, Search } from 'lucide-react'

interface WelcomeModalProps {
  onComplete?: () => void
}

export function WelcomeModal({ onComplete }: WelcomeModalProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    // Check if user has seen the welcome modal
    const hasSeenWelcome = localStorage.getItem('hasSeenWelcome')
    if (!hasSeenWelcome) {
      setIsOpen(true)
    }
  }, [])

  const handleClose = () => {
    localStorage.setItem('hasSeenWelcome', 'true')
    setIsOpen(false)
    onComplete?.()
  }

  const features = [
    {
      icon: Database,
      title: 'Extraer datos del RENEC',
      description: 'Cosecha información actualizada de estándares de competencia'
    },
    {
      icon: Search,
      title: 'Buscar y filtrar',
      description: 'Encuentra rápidamente la información que necesitas'
    },
    {
      icon: Download,
      title: 'Exportar en múltiples formatos',
      description: 'Descarga datos en Excel, CSV, JSON o XML'
    },
    {
      icon: Sparkles,
      title: 'Seguir cambios',
      description: 'Mantente al día con las actualizaciones del registro'
    }
  ]

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-overlay-bg z-50"
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-surface-elevated rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-default">
                <h2 className="text-2xl font-bold text-primary flex items-center gap-2">
                  <Sparkles className="text-accent" />
                  ¡Bienvenido al Cosechador RENEC!
                </h2>
                <button
                  onClick={handleClose}
                  className="p-2 rounded-lg hover:bg-secondary transition-colors"
                  aria-label="Cerrar"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Content */}
              <div className="p-6">
                <p className="text-lg text-secondary mb-8">
                  Esta herramienta le permite extraer y analizar datos del Registro Nacional 
                  de Estándares de Competencia de manera fácil y eficiente.
                </p>

                <div className="mb-8">
                  <h3 className="text-lg font-semibold mb-4">¿Qué puede hacer?</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {features.map((feature, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex gap-3 p-4 rounded-lg bg-surface hover:bg-secondary transition-colors"
                      >
                        <feature.icon className="text-accent flex-shrink-0" size={24} />
                        <div>
                          <h4 className="font-medium text-primary">{feature.title}</h4>
                          <p className="text-sm text-secondary">{feature.description}</p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Call to Action */}
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <button
                    onClick={handleClose}
                    className="px-6 py-3 bg-primary hover:bg-primary-hover text-primary-text rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    Comenzar el recorrido
                    <ChevronRight size={20} />
                  </button>
                  <button
                    onClick={handleClose}
                    className="px-6 py-3 bg-secondary hover:bg-secondary-hover text-secondary-text rounded-lg font-medium transition-colors"
                  >
                    Ya conozco la herramienta
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}