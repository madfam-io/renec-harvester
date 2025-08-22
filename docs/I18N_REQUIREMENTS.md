# Internationalization (i18n) Requirements - Spanish First

## 🌎 Overview

RENEC Harvester will be a bilingual application with **Spanish as the primary language**, reflecting the tool's focus on Mexican government data and its primary user base.

## 🎯 Language Strategy

### Primary Language: Spanish (es-MX)
- Default language for all users
- Complete translations for all features
- Mexican Spanish dialect and terminology
- Government/technical terminology aligned with CONOCER

### Secondary Language: English (en-US)
- Full translation support
- Technical documentation
- International accessibility

## 📚 Translation Scope

### 1. **User Interface**
All visible text elements must be translatable:
- Navigation menus
- Buttons and actions
- Form labels and placeholders
- Error messages
- Success notifications
- Loading states
- Empty states

### 2. **Content Areas**

#### Dashboard
```javascript
{
  "dashboard": {
    "title": "Panel de Control",
    "subtitle": "Resumen del Cosechador RENEC",
    "stats": {
      "totalStandards": "Estándares Totales",
      "activeCertifiers": "Certificadores Activos",
      "lastUpdate": "Última Actualización",
      "dataQuality": "Calidad de Datos"
    }
  }
}
```

#### Harvester Controls
```javascript
{
  "harvester": {
    "title": "Control del Cosechador",
    "actions": {
      "start": "Iniciar Cosecha",
      "stop": "Detener",
      "pause": "Pausar",
      "resume": "Reanudar"
    },
    "status": {
      "idle": "Inactivo",
      "running": "Ejecutándose",
      "paused": "Pausado",
      "completed": "Completado",
      "error": "Error"
    },
    "config": {
      "mode": "Modo de Operación",
      "crawl": "Mapeo",
      "harvest": "Cosecha",
      "concurrent": "Solicitudes Concurrentes",
      "delay": "Retraso entre Solicitudes"
    }
  }
}
```

#### Data Management
```javascript
{
  "data": {
    "title": "Gestión de Datos",
    "search": {
      "placeholder": "Buscar estándares, certificadores...",
      "filters": "Filtros",
      "results": "Resultados"
    },
    "export": {
      "title": "Exportar Datos",
      "format": "Formato",
      "dateRange": "Rango de Fechas",
      "download": "Descargar"
    },
    "import": {
      "title": "Importar Datos",
      "selectFile": "Seleccionar Archivo",
      "validate": "Validar",
      "process": "Procesar"
    }
  }
}
```

### 3. **Technical Terms Dictionary**

| English | Spanish | Context |
|---------|---------|---------|
| Harvester | Cosechador | Main tool |
| Crawl | Mapear | Site mapping |
| Harvest | Cosechar | Data extraction |
| Standard | Estándar | EC Standard |
| Certifier | Certificador | ECE/OC |
| Center | Centro | Evaluation center |
| Sector | Sector | Industry sector |
| Committee | Comité | Technical committee |
| Spider | Araña | Web crawler |
| Endpoint | Punto de acceso | API endpoint |
| Rate limit | Límite de frecuencia | Request limiting |
| Batch | Lote | Group processing |
| Pipeline | Flujo de proceso | Data pipeline |
| Validation | Validación | Data validation |
| Schema | Esquema | Data structure |

### 4. **Error Messages**

#### Network Errors
```javascript
{
  "errors": {
    "network": {
      "timeout": "Tiempo de espera agotado. Por favor, intente nuevamente.",
      "offline": "Sin conexión a internet. Verifique su conexión.",
      "serverError": "Error del servidor. Contacte al administrador.",
      "notFound": "Recurso no encontrado.",
      "forbidden": "Acceso denegado. Verifique sus permisos."
    }
  }
}
```

#### Validation Errors
```javascript
{
  "errors": {
    "validation": {
      "required": "Este campo es obligatorio",
      "invalidFormat": "Formato inválido",
      "minLength": "Mínimo {min} caracteres",
      "maxLength": "Máximo {max} caracteres",
      "invalidEmail": "Correo electrónico inválido",
      "invalidDate": "Fecha inválida"
    }
  }
}
```

### 5. **Help & Documentation**

#### Tooltips
```javascript
{
  "tooltips": {
    "crawlMode": "Mapea la estructura del sitio sin extraer datos",
    "harvestMode": "Extrae todos los datos disponibles",
    "concurrentRequests": "Número de solicitudes simultáneas (1-10)",
    "exportFormat": "Seleccione el formato de archivo para exportar"
  }
}
```

#### Onboarding
```javascript
{
  "onboarding": {
    "welcome": {
      "title": "Bienvenido al Cosechador RENEC",
      "description": "Esta herramienta le permite extraer y analizar datos del Registro Nacional de Estándares de Competencia.",
      "getStarted": "Comenzar",
      "skipTour": "Omitir tour"
    },
    "steps": [
      {
        "title": "Configure el Cosechador",
        "content": "Seleccione el modo de operación y ajuste los parámetros según sus necesidades."
      },
      {
        "title": "Inicie la Cosecha",
        "content": "Haga clic en 'Iniciar Cosecha' para comenzar la extracción de datos."
      },
      {
        "title": "Explore los Datos",
        "content": "Use los filtros y búsqueda para encontrar la información que necesita."
      },
      {
        "title": "Exporte Resultados",
        "content": "Descargue los datos en el formato que prefiera."
      }
    ]
  }
}
```

## 🔧 Implementation Guidelines

### 1. **File Organization**
```
/locales
  /es-MX
    - common.json      # Shared translations
    - dashboard.json   # Dashboard specific
    - harvester.json   # Harvester features
    - data.json        # Data management
    - errors.json      # Error messages
    - help.json        # Help content
  /en-US
    - (same structure)
```

### 2. **Translation Keys**
- Use nested objects for organization
- Keep keys descriptive but concise
- Use camelCase for keys
- Support interpolation for dynamic values

### 3. **Date/Time Formatting**
```javascript
// Spanish format
{
  "dateFormat": "DD/MM/YYYY",
  "timeFormat": "HH:mm",
  "dateTimeFormat": "DD/MM/YYYY HH:mm",
  "relativeTimes": {
    "justNow": "justo ahora",
    "minutesAgo": "hace {minutes} minutos",
    "hoursAgo": "hace {hours} horas",
    "yesterday": "ayer",
    "daysAgo": "hace {days} días"
  }
}
```

### 4. **Number Formatting**
```javascript
// Spanish number format
{
  "numbers": {
    "decimal": ",",
    "thousand": ".",
    "currency": "MXN"
  }
}
```

## 🌐 Language Switching

### UI Elements
- Language selector in header
- Flag icons (🇲🇽 🇺🇸)
- Persistent preference
- Instant switching without reload

### Detection Priority
1. User preference (localStorage)
2. Browser language
3. Default: Spanish (es-MX)

## ✅ Quality Standards

### Translation Guidelines
1. **Consistency**: Use CONOCER's official terminology
2. **Clarity**: Avoid literal translations that don't make sense
3. **Conciseness**: Keep translations brief for UI elements
4. **Context**: Consider where text appears
5. **Tone**: Professional but friendly

### Review Process
1. Native speaker review
2. Technical accuracy check
3. UI/UX context verification
4. User testing with target audience

## 📱 Responsive Considerations

### Text Expansion
- Spanish text can be 15-30% longer than English
- Design with flexibility for text expansion
- Test all breakpoints with both languages

### RTL Support
- Not required for Spanish/English
- Structure ready for future RTL languages

## 🔄 Maintenance

### Translation Updates
- Version control for translation files
- Change tracking for updates
- Regular review cycles
- User feedback integration

### Missing Translations
- Fallback to key name (development)
- Fallback to English (production)
- Log missing translations
- Regular audit reports

---

*Last updated: August 22, 2025*  
*Primary Language: Spanish (es-MX)*  
*Secondary Language: English (en-US)*