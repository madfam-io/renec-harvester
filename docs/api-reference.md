# RENEC Harvester API Reference

## 🔗 Base URL

```
http://localhost:8000
```

## 📋 API Overview

The RENEC Harvester API provides REST endpoints for:
- **Spider Management**: Control scraping operations
- **Data Access**: Query and export collected data
- **System Monitoring**: Performance metrics and health status

## 🕷️ Spider Management

### Start Spider

Start a scraping operation with custom configuration.

**Endpoint:** `POST /api/spider/start`

**Request Body:**
```json
{
  "mode": "crawl",
  "max_depth": 5,
  "concurrent_requests": 8,
  "download_delay": 0.5,
  "retry_times": 3,
  "respect_robots_txt": true,
  "enable_caching": true,
  "target_components": {
    "ec_standards": true,
    "certificadores": true,
    "evaluation_centers": true,
    "courses": true,
    "sectors": true,
    "committees": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Spider started successfully",
  "status": "running",
  "config": { /* echoed config */ }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/spider/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "harvest", "concurrent_requests": 10}'
```

### Stop Spider

Stop the currently running spider.

**Endpoint:** `POST /api/spider/stop`

**Response:**
```json
{
  "success": true,
  "message": "Spider stopped successfully", 
  "status": "idle"
}
```

### Pause Spider

Temporarily pause the running spider.

**Endpoint:** `POST /api/spider/pause`

**Response:**
```json
{
  "success": true,
  "message": "Spider paused successfully",
  "status": "paused"
}
```

### Resume Spider

Resume a paused spider.

**Endpoint:** `POST /api/spider/resume`

**Response:**
```json
{
  "success": true,
  "message": "Spider resumed successfully",
  "status": "running"
}
```

### Reset Spider

Reset spider state and clear cached data.

**Endpoint:** `POST /api/spider/reset`

**Response:**
```json
{
  "success": true,
  "message": "Spider reset successfully",
  "status": "idle"
}
```

### Get Spider Status

Get current spider status and configuration.

**Endpoint:** `GET /api/spider/status`

**Response:**
```json
{
  "success": true,
  "message": "Status retrieved successfully",
  "status": "running",
  "config": {
    "mode": "harvest",
    "max_depth": 5,
    "concurrent_requests": 8,
    "download_delay": 0.5,
    "retry_times": 3,
    "respect_robots_txt": true,
    "enable_caching": true,
    "target_components": {
      "ec_standards": true,
      "certificadores": true,
      "evaluation_centers": true,
      "courses": true,
      "sectors": true,
      "committees": false
    }
  }
}
```

## 📊 Statistics and Monitoring

### Get Spider Statistics

Get real-time spider performance metrics.

**Endpoint:** `GET /api/stats`

**Response:**
```json
{
  "total_requests": 2453,
  "successful_requests": 2341,
  "failed_requests": 112,
  "items_scraped": 1876,
  "current_speed": 12.5,
  "avg_response_time": 145.2,
  "queue_size": 34,
  "uptime": "02:15:42",
  "status": "running",
  "start_time": "2024-08-21T08:00:00Z",
  "last_activity": "2024-08-21T10:15:42Z"
}
```

### Get System Health

Get system health status including database and Redis.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "database": "healthy",
  "redis": "healthy", 
  "spider": "running",
  "memory_usage": 45.2,
  "disk_usage": 23.8
}
```

### Get Metrics History

Get historical performance metrics.

**Endpoint:** `GET /api/metrics/history`

**Query Parameters:**
- `hours` (optional): Number of hours of history (default: 24)

**Response:**
```json
{
  "data": [
    {
      "timestamp": "2024-08-21T08:00:00Z",
      "requests": 45,
      "items": 12,
      "errors": 2,
      "response_time": 150
    },
    {
      "timestamp": "2024-08-21T08:05:00Z", 
      "requests": 52,
      "items": 15,
      "errors": 1,
      "response_time": 132
    }
  ],
  "period": "24 hours",
  "total_points": 288
}
```

### Get Component Metrics

Get per-component scraping progress.

**Endpoint:** `GET /api/metrics/components`

**Response:**
```json
{
  "components": [
    {
      "name": "EC Standards",
      "scraped": 1250,
      "total": 1500,
      "last_updated": "2024-08-21T10:15:00Z",
      "success_rate": 94.5,
      "avg_response_time": 145
    },
    {
      "name": "Certificadores",
      "scraped": 890,
      "total": 1200,
      "last_updated": "2024-08-21T10:00:00Z",
      "success_rate": 97.8,
      "avg_response_time": 132
    }
  ],
  "last_updated": "2024-08-21T10:15:00Z",
  "total_progress": 73.2
}
```

### Get Error Metrics

Get recent error statistics and details.

**Endpoint:** `GET /api/metrics/errors`

**Query Parameters:**
- `limit` (optional): Maximum number of errors to return (default: 50)

**Response:**
```json
{
  "errors": [
    {
      "timestamp": "2024-08-21T10:00:00Z",
      "type": "HTTP_ERROR",
      "code": "404",
      "url": "https://conocer.gob.mx/RENEC/controlador.do?comp=EC&ec=123",
      "message": "Page not found",
      "count": 3
    },
    {
      "timestamp": "2024-08-21T09:45:00Z",
      "type": "TIMEOUT_ERROR",
      "code": "TIMEOUT", 
      "url": "https://conocer.gob.mx/RENEC/controlador.do?comp=CERT&id=456",
      "message": "Request timeout after 30 seconds",
      "count": 1
    }
  ],
  "total_errors": 47,
  "error_rate": 2.1,
  "last_updated": "2024-08-21T10:15:00Z"
}
```

## 🗄️ Data Access

### Get Data

Get paginated data with optional filtering and search.

**Endpoint:** `GET /api/data`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 50, max: 100)
- `type` (optional): Filter by data type (`ec_standard`, `certificador`, `evaluation_center`, `course`, `sector`)
- `status` (optional): Filter by status (`active`, `pending`, `error`)
- `search` (optional): Search by title or code

**Response:**
```json
{
  "items": [
    {
      "id": "1",
      "type": "ec_standard",
      "title": "Instalación de sistemas de aire acondicionado",
      "code": "EC0221",
      "sector": "Construcción",
      "last_updated": "2024-08-21T10:00:00Z",
      "status": "active"
    }
  ],
  "total": 4765,
  "page": 1,
  "per_page": 50
}
```

**Examples:**
```bash
# Get first page of data
curl "http://localhost:8000/api/data"

# Search for specific terms
curl "http://localhost:8000/api/data?search=soldadura&type=course"

# Get active EC standards only
curl "http://localhost:8000/api/data?type=ec_standard&status=active"
```

### Get Data Item

Get detailed information for a specific data item.

**Endpoint:** `GET /api/data/{item_id}`

**Response:**
```json
{
  "id": "1",
  "type": "ec_standard",
  "title": "Instalación de sistemas de aire acondicionado",
  "code": "EC0221",
  "sector": "Construcción",
  "last_updated": "2024-08-21T10:00:00Z",
  "status": "active",
  "data": {
    "description": "Estándar para la instalación y mantenimiento de sistemas de aire acondicionado",
    "competencies": [
      "Diagnóstico de sistemas",
      "Instalación de equipos", 
      "Mantenimiento preventivo"
    ],
    "duration_hours": 120,
    "certification_body": "CONOCER",
    "validity_years": 3
  }
}
```

### Export Data

Export data in various formats.

**Endpoint:** `GET /api/export`

**Query Parameters:**
- `format`: Export format (`json` or `csv`)
- `type` (optional): Filter by data type
- `status` (optional): Filter by status

**Response:** File download with appropriate MIME type

**Examples:**
```bash
# Export all data as JSON
curl "http://localhost:8000/api/export?format=json" -o export.json

# Export only EC standards as CSV
curl "http://localhost:8000/api/export?format=csv&type=ec_standard" -o ec_standards.csv
```

### Get Data Summary

Get summary statistics of available data.

**Endpoint:** `GET /api/summary`

**Response:**
```json
{
  "total_items": 4765,
  "by_type": {
    "ec_standard": 1250,
    "certificador": 890,
    "evaluation_center": 450,
    "course": 2100,
    "sector": 75
  },
  "by_status": {
    "active": 4234,
    "pending": 456,
    "error": 75
  },
  "by_sector": {
    "Construcción": 1200,
    "Educación": 890,
    "Manufactura": 1100,
    "Tecnología": 675,
    "Servicios": 900
  },
  "last_updated": "2024-08-21T10:15:00Z",
  "data_freshness": {
    "last_24h": 234,
    "last_week": 1456,
    "last_month": 3890
  }
}
```

## 🔧 System Endpoints

### Root Endpoint

Get API information.

**Endpoint:** `GET /`

**Response:**
```json
{
  "name": "RENEC Harvester API",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs"
}
```

### Health Check

Simple health check endpoint.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy"
}
```

## 📝 Data Models

### Spider Configuration

```typescript
interface SpiderConfig {
  mode: "crawl" | "harvest"
  max_depth: number        // 1-10
  concurrent_requests: number  // 1-20
  download_delay: number   // 0.0-5.0 seconds
  retry_times: number      // 0-10
  respect_robots_txt: boolean
  enable_caching: boolean
  target_components: {
    ec_standards: boolean
    certificadores: boolean
    evaluation_centers: boolean
    courses: boolean
    sectors: boolean
    committees: boolean
  }
}
```

### Spider Statistics

```typescript
interface SpiderStats {
  total_requests: number
  successful_requests: number
  failed_requests: number
  items_scraped: number
  current_speed: number    // items per minute
  avg_response_time: number // milliseconds
  queue_size: number
  uptime: string          // "HH:MM:SS"
  status: "idle" | "running" | "paused" | "error"
  start_time?: string     // ISO datetime
  last_activity?: string  // ISO datetime
}
```

### Data Item

```typescript
interface DataItem {
  id: string
  type: string
  title: string
  code: string
  sector?: string
  last_updated: string    // ISO datetime
  status: string
  data?: Record<string, any>
}
```

## 🚨 Error Responses

All endpoints return standardized error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `400 Bad Request`: Invalid parameters or spider already running
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

## 🔐 Authentication

Currently, the API does not require authentication. In production environments, consider implementing:
- API key authentication
- OAuth 2.0 / JWT tokens
- IP whitelisting
- Rate limiting

## 🎯 Usage Examples

### Complete Harvesting Workflow

```bash
# 1. Check current status
curl http://localhost:8000/api/spider/status

# 2. Start harvesting with custom config
curl -X POST http://localhost:8000/api/spider/start \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "harvest",
    "concurrent_requests": 8,
    "download_delay": 1.0,
    "target_components": {
      "ec_standards": true,
      "certificadores": true,
      "evaluation_centers": false,
      "courses": false,
      "sectors": true,
      "committees": false
    }
  }'

# 3. Monitor progress
curl http://localhost:8000/api/stats

# 4. Check component progress
curl http://localhost:8000/api/metrics/components

# 5. Export results when complete
curl "http://localhost:8000/api/export?format=json" -o harvest_results.json

# 6. Stop spider
curl -X POST http://localhost:8000/api/spider/stop
```

### Data Analysis Workflow

```bash
# Get data summary
curl http://localhost:8000/api/summary

# Search for specific standards
curl "http://localhost:8000/api/data?search=soldadura&type=ec_standard"

# Get detailed information
curl http://localhost:8000/api/data/1

# Export filtered data
curl "http://localhost:8000/api/export?format=csv&type=certificador&status=active" \
  -o active_certificadores.csv
```

## 📚 Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger documentation where you can:
- Try out all endpoints
- See detailed request/response schemas
- Generate code examples in multiple languages
- Test authentication and error scenarios

The interactive docs are automatically generated from the API code and are always up-to-date.