# RENEC Harvester Web Interface User Guide

## 🌐 Overview

The RENEC Harvester Web Interface provides a comprehensive dashboard for managing data harvesting operations from México's RENEC platform. This guide covers all features and workflows available through the web interface.

## 🚀 Quick Start

### Accessing the Interface

1. **Start the web interface:**
   ```bash
   ./start-ui.sh
   ```

2. **Open your browser and navigate to:**
   - **Main Interface**: http://localhost:3001
   - **API Documentation**: http://localhost:8000/docs

3. **The interface will display the main dashboard with three tabs:**
   - **Scraping Controls**: Configure and manage harvesting operations
   - **Monitoring**: Real-time performance metrics and system health
   - **Data Explorer**: Browse, search, and export collected data

## 📊 Scraping Controls

### Starting a Harvest Operation

1. **Navigate to the "Scraping Controls" tab**
2. **Configure harvesting parameters:**

   #### Basic Settings
   - **Scraping Mode**:
     - `Crawl`: Discover and map the RENEC site structure
     - `Harvest`: Extract data from known endpoints
   
   - **Max Crawl Depth**: How deep to crawl the site (1-10 levels)
   - **Concurrent Requests**: Number of parallel requests (1-20)
   - **Download Delay**: Delay between requests in seconds (0-5)

   #### Target Components
   Select which RENEC components to harvest:
   - ✅ **EC Standards**: Competency standards
   - ✅ **Certificadores**: Certification entities (ECE/OC)
   - ✅ **Evaluation Centers**: Testing centers
   - ✅ **Courses**: Training programs
   - ✅ **Sectors**: Industry sectors
   - ⚪ **Committees**: Technical committees (optional)

   #### Advanced Options
   - **Respect robots.txt**: Follow site crawling guidelines
   - **Enable caching**: Use Redis caching for performance

3. **Click "Start Scraping"** to begin the operation

### Managing Active Operations

- **Pause/Resume**: Temporarily halt operations without losing progress
- **Stop**: Completely stop the current operation
- **Reset**: Clear all cached data and reset the spider state

### Configuration Persistence

- **Save**: Store current configuration as default
- Settings are automatically applied to new scraping sessions

## 📈 Monitoring Dashboard

### Key Metrics Overview

The dashboard displays four main performance indicators:

1. **Total Requests**
   - Count of HTTP requests made
   - Success/failure breakdown
   - Real-time updates every 5 seconds

2. **Items Scraped**
   - Number of data records extracted
   - Current scraping speed (items/minute)
   - Progress toward completion

3. **Average Response Time**
   - Server response performance in milliseconds
   - Queue size for pending requests
   - Network performance indicators

4. **System Uptime**
   - How long the current session has been running
   - Overall system status
   - Service health indicators

### Performance Charts

#### Recent Activity Timeline
- **Requests**: HTTP requests over time
- **Items**: Data extraction rate
- **Errors**: Failed request tracking
- Updates every 5 minutes with the latest data

#### Component Progress Bars
Track harvesting progress for each RENEC component:
- **Visual progress bars** showing completion percentage
- **Numerical indicators** (scraped/total items)
- **Color-coded status** for quick assessment

### System Health Monitoring

Monitor the health of core system components:

- **Database**: PostgreSQL connection and performance
- **Redis Cache**: Caching system status
- **Memory Usage**: System resource utilization
- **Response Times**: API and scraping performance

#### Health Status Indicators
- 🟢 **Green**: Healthy, operating normally
- 🟡 **Yellow**: Warning, may need attention
- 🔴 **Red**: Error, requires immediate action

## 🗄️ Data Explorer

### Browsing Collected Data

#### Search and Filter Interface

1. **Search Bar**
   - Search by title or code (e.g., "EC0221", "Soldadura")
   - Real-time filtering as you type
   - Case-insensitive search

2. **Filter Controls**
   - **Type Filter**: Filter by data type
     - EC Standards
     - Certificadores
     - Evaluation Centers
     - Courses
     - Sectors
   
   - **Status Filter**: Filter by record status
     - Active
     - Pending
     - Error

3. **Refresh Button**: Update data from the latest harvest

#### Data Table

The main data table displays:

| Column | Description |
|--------|-------------|
| **Type** | Category of data record |
| **Title** | Full name or description |
| **Code** | Unique identifier (e.g., EC0221, CERT001) |
| **Sector** | Industry sector classification |
| **Status** | Current record status |
| **Last Updated** | When the record was last modified |
| **Actions** | View detailed information |

#### Data Type Color Coding
- 🔵 **Blue**: EC Standards
- 🟣 **Purple**: Certificadores
- 🟠 **Orange**: Courses
- 🟦 **Indigo**: Evaluation Centers
- 🌸 **Pink**: Sectors

### Detailed Record View

Click the **eye icon** (👁️) to view detailed information for any record:

- **Complete metadata** for the selected item
- **Relationships** to other records
- **Source URLs** and provenance information
- **Full data payload** in structured format

### Data Export

#### Export Formats

1. **JSON Export**
   - Complete data with metadata
   - Structured format for API consumption
   - Includes export timestamp and filters applied

2. **CSV Export**
   - Tabular format for spreadsheet analysis
   - All visible columns included
   - Compatible with Excel, Google Sheets

#### Export Process

1. **Apply desired filters** to select data subset
2. **Click export button** (JSON or CSV)
3. **File downloads automatically** with timestamp
4. **Filename format**: `renec_export_YYYYMMDD_HHMMSS.{format}`

#### Export Contents

Exported files include:
- **Metadata section**: Export date, total items, applied filters
- **Data section**: All records matching current filters
- **Provenance information**: Source URLs, last updated timestamps

## ⚙️ System Configuration

### Environment Variables

Key configuration options available:

```bash
# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# Database Configuration
DATABASE_URL=postgresql://renec:password@localhost:5432/renec_harvester
REDIS_URL=redis://localhost:6379/0

# UI Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Customizing the Interface

#### Port Configuration
- **Frontend**: Default port 3001 (configurable in `ui/package.json`)
- **API**: Default port 8000 (configurable via environment variables)

#### Performance Tuning
- **Concurrent Requests**: Adjust based on your system capabilities
- **Download Delay**: Increase for politeness, decrease for speed
- **Caching**: Enable for better performance on repeated operations

## 🔧 Troubleshooting

### Common Issues

#### Interface Won't Load
1. **Check services are running:**
   ```bash
   # Check if ports are in use
   lsof -i :3001  # Frontend
   lsof -i :8000  # API
   ```

2. **Restart services:**
   ```bash
   ./start-ui.sh
   ```

#### Scraping Won't Start
1. **Verify Docker services:**
   ```bash
   docker ps  # Check PostgreSQL and Redis are running
   ```

2. **Check browser installation:**
   ```bash
   playwright install --with-deps
   ```

#### No Data Appears
1. **Run a test harvest:**
   ```bash
   source venv/bin/activate
   scrapy crawl renec -a mode=crawl -a max_depth=1
   ```

2. **Check database connectivity** in the Monitoring tab

#### Performance Issues
1. **Reduce concurrent requests** in Scraping Controls
2. **Increase download delay** for politeness
3. **Monitor system resources** in the dashboard

### Getting Help

1. **Check the logs** in the terminal where services are running
2. **Review the troubleshooting guide** (`docs/troubleshooting.md`)
3. **Visit API documentation** at http://localhost:8000/docs
4. **Check system health** in the Monitoring dashboard

## 💡 Best Practices

### Ethical Scraping
- **Use reasonable delays** between requests (0.5-2 seconds)
- **Limit concurrent requests** (8-12 max)
- **Monitor for rate limiting** in the dashboard
- **Respect the target site's resources**

### Data Management
- **Regular exports** of important data
- **Monitor data quality** through the dashboard
- **Review error logs** for failed extractions
- **Maintain data freshness** with scheduled runs

### System Maintenance
- **Monitor system health** regularly
- **Check disk space** for artifacts and logs
- **Update browser dependencies** periodically
- **Review and clean old harvest data**

## 🎯 Advanced Features

### API Integration

The web interface is built on a REST API that you can also use directly:

```bash
# Get spider status
curl http://localhost:8000/api/spider/status

# Start harvesting
curl -X POST http://localhost:8000/api/spider/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "harvest", "concurrent_requests": 8}'

# Get statistics
curl http://localhost:8000/api/stats

# Export data programmatically
curl "http://localhost:8000/api/export?format=json" -o export.json
```

### Custom Monitoring

Set up external monitoring by polling these endpoints:
- **Health check**: `GET /health`
- **System metrics**: `GET /api/stats`
- **Component progress**: `GET /api/metrics/components`

### Automation

The interface supports automated workflows:
1. **Start harvesting** via API
2. **Monitor progress** through metrics endpoints
3. **Export results** when complete
4. **Schedule regular operations** using cron jobs

This completes the comprehensive user guide for the RENEC Harvester Web Interface. The interface provides full control over data harvesting operations while maintaining transparency and ease of use.