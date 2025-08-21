# RENEC Harvester API Documentation

## Overview

The RENEC Harvester API provides programmatic access to México's National Registry of Competency Standards (RENEC) data. This RESTful API offers endpoints for querying EC standards, certificadores, evaluation centers, sectors, and their relationships.

**Base URL**: `https://api.renec-harvester.example.com/api/v1`

## Authentication

Currently, the API is read-only and does not require authentication. Future versions will implement JWT-based authentication for write operations.

## Rate Limiting

- **Default limit**: 100 requests per minute per IP
- **Burst limit**: 20 requests
- **Headers**: Rate limit info provided in response headers:
  - `X-RateLimit-Limit`: Request limit per minute
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Unix timestamp for limit reset

## Common Parameters

### Pagination
Most list endpoints support pagination:
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 100, max: 1000)

### Search
- `search` (string): Search term for text fields
- `q` (string): Query parameter for cross-entity search

## Endpoints

### EC Standards

#### List EC Standards
```http
GET /ec-standards
```

**Query Parameters:**
- `skip` (int): Pagination offset
- `limit` (int): Page size
- `vigente` (bool): Filter by active status
- `sector_id` (int): Filter by sector
- `search` (string): Search in code and title

**Response:**
```json
[
  {
    "ec_clave": "EC0217",
    "titulo": "Impartición de cursos de formación del capital humano de manera presencial grupal",
    "version": "3.00",
    "vigente": true,
    "sector": "Educación",
    "sector_id": 1,
    "nivel": "3",
    "duracion_horas": 40,
    "last_seen": "2025-08-21T10:30:00Z"
  }
]
```

#### Get EC Standard Details
```http
GET /ec-standards/{ec_clave}
```

**Path Parameters:**
- `ec_clave` (string): EC standard code

**Response:**
```json
{
  "ec_clave": "EC0217",
  "titulo": "Impartición de cursos de formación del capital humano de manera presencial grupal",
  "version": "3.00",
  "vigente": true,
  "sector": "Educación",
  "sector_id": 1,
  "comite": "Gestión y desarrollo de capital humano",
  "comite_id": 1,
  "descripcion": "El estándar de competencia describe...",
  "competencias": ["Competencia 1", "Competencia 2"],
  "nivel": "3",
  "duracion_horas": 40,
  "tipo_norma": "Nacional",
  "fecha_publicacion": "2012-07-27",
  "fecha_vigencia": "2017-07-27",
  "perfil_evaluador": "Requisitos académicos y laborales...",
  "criterios_evaluacion": ["Criterio 1", "Criterio 2"],
  "renec_url": "https://conocer.gob.mx/RENEC/...",
  "first_seen": "2025-08-01T00:00:00Z",
  "last_seen": "2025-08-21T10:30:00Z",
  "certificadores": [
    {
      "cert_id": "ECE001-99",
      "tipo": "ECE",
      "nombre_legal": "CONOCER",
      "estado": "Ciudad de México"
    }
  ]
}
```

#### Get EC Standard Certificadores
```http
GET /ec-standards/{ec_clave}/certificadores
```

Returns all certificadores that can accredit this EC standard.

#### Get EC Standard Centros
```http
GET /ec-standards/{ec_clave}/centros
```

**Query Parameters:**
- `estado_inegi` (string): Filter by INEGI state code

### Certificadores

#### List Certificadores
```http
GET /certificadores
```

**Query Parameters:**
- `skip`, `limit`: Pagination
- `tipo` (string): ECE or OC
- `estado_inegi` (string): State code
- `estatus` (string): Vigente or Cancelado
- `search` (string): Search text

#### Get Certificador Details
```http
GET /certificadores/{cert_id}
```

#### Get Certificador EC Standards
```http
GET /certificadores/{cert_id}/ec-standards
```

Returns all EC standards this certificador can accredit (ECE only).

#### Get Certificadores by State
```http
GET /certificadores/by-state/{estado_inegi}
```

#### Get Certificador Statistics
```http
GET /certificadores/stats/by-state
```

Returns national and state-level statistics.

### Centros (Evaluation Centers)

#### List Centros
```http
GET /centros
```

**Query Parameters:**
- `skip`, `limit`: Pagination
- `estado_inegi` (string): State code
- `municipio` (string): Municipality
- `search` (string): Search text

#### Get Centro Details
```http
GET /centros/{centro_id}
```

#### Get Centro EC Standards
```http
GET /centros/{centro_id}/ec-standards
```

#### Find Nearby Centros
```http
GET /centros/nearby
```

**Query Parameters:**
- `estado_inegi` (string, required): State code
- `municipio` (string): Municipality name
- `limit` (int): Max results

### Sectores & Comités

#### List Sectores
```http
GET /sectores
```

#### Get Sector Details
```http
GET /sectores/{sector_id}
```

#### Get Sector EC Standards
```http
GET /sectores/{sector_id}/ec-standards
```

#### List Comités
```http
GET /comites
```

**Query Parameters:**
- `sector_id` (int): Filter by sector
- `search` (string): Search in name

#### Get Comité Details
```http
GET /comites/{comite_id}
```

### Search

#### Cross-Entity Search
```http
GET /search
```

**Query Parameters:**
- `q` (string, required): Search query (min 2 chars)
- `entity_types` (string): Comma-separated types
- `limit` (int): Max results per type

**Response:**
```json
{
  "query": "seguridad",
  "total_results": 42,
  "results": {
    "ec_standards": {
      "count": 15,
      "items": [...]
    },
    "certificadores": {
      "count": 8,
      "items": [...]
    }
  }
}
```

#### Search Suggestions
```http
GET /search/suggest
```

**Query Parameters:**
- `q` (string, required): Partial query
- `entity_type` (string, required): Entity type
- `limit` (int): Max suggestions

#### Location-Based Search
```http
GET /search/by-location
```

**Query Parameters:**
- `estado_inegi` (string, required): State code
- `municipio` (string): Municipality
- `entity_types` (string): Types to search

#### Related Entities
```http
GET /search/related/{entity_type}/{entity_id}
```

Find all entities related to a specific entity.

## Response Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Error Response Format

```json
{
  "detail": "Error message",
  "type": "error_type",
  "title": "Error Title",
  "status": 400
}
```

## Data Types

### INEGI State Codes

| Code | State |
|------|-------|
| 01 | Aguascalientes |
| 02 | Baja California |
| 09 | Ciudad de México |
| 15 | México |
| ... | ... |

### Entity Types

- `ec_standards`: EC Standards
- `certificadores`: Certification entities
- `centros`: Evaluation centers
- `sectores`: Productive sectors
- `comites`: Management committees

## Examples

### Search for EC Standards in Education Sector
```bash
curl "https://api.renec-harvester.example.com/api/v1/ec-standards?sector_id=1&vigente=true"
```

### Find Certificadores in Mexico City
```bash
curl "https://api.renec-harvester.example.com/api/v1/certificadores?estado_inegi=09&tipo=ECE"
```

### Search Across All Entities
```bash
curl "https://api.renec-harvester.example.com/api/v1/search?q=informatica&limit=5"
```

### Get Nearby Evaluation Centers
```bash
curl "https://api.renec-harvester.example.com/api/v1/centros/nearby?estado_inegi=09&municipio=Benito%20Juarez"
```

## Webhooks (Future)

Future versions will support webhooks for:
- New EC standards published
- Certificador status changes
- Daily harvest completion

## SDKs

Official SDKs are planned for:
- Python
- JavaScript/TypeScript
- Java
- Go

## Support

- **Documentation**: https://docs.renec-harvester.example.com
- **Status Page**: https://status.renec-harvester.example.com
- **GitHub**: https://github.com/your-org/renec-harvester