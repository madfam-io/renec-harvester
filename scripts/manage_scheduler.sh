#!/bin/bash

# RENEC Harvester Scheduler Management Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_usage() {
    echo "Usage: $0 {start|stop|restart|status|logs|test}"
    echo ""
    echo "Commands:"
    echo "  start   - Start the scheduler services"
    echo "  stop    - Stop the scheduler services"
    echo "  restart - Restart the scheduler services"
    echo "  status  - Show scheduler status"
    echo "  logs    - Tail scheduler logs"
    echo "  test    - Run a test harvest"
}

start_scheduler() {
    echo -e "${GREEN}Starting RENEC scheduler...${NC}"
    
    # Start with docker-compose
    if command -v docker-compose &> /dev/null; then
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.scheduler.yml up -d
        echo -e "${GREEN}Scheduler started with Docker Compose${NC}"
    else
        # Fallback to manual start
        echo -e "${YELLOW}Starting scheduler manually...${NC}"
        
        # Start Celery Beat
        celery -A src.scheduler.daily_probe beat \
            --loglevel=info \
            --pidfile=/tmp/celerybeat.pid \
            --detach
        
        # Start Celery Workers
        celery -A src.scheduler.daily_probe worker \
            --loglevel=info \
            --queues=harvest,monitoring \
            --pidfile=/tmp/celeryworker.pid \
            --detach
        
        echo -e "${GREEN}Scheduler started manually${NC}"
    fi
}

stop_scheduler() {
    echo -e "${YELLOW}Stopping RENEC scheduler...${NC}"
    
    if command -v docker-compose &> /dev/null; then
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.scheduler.yml down
        echo -e "${GREEN}Scheduler stopped${NC}"
    else
        # Stop manual processes
        if [ -f /tmp/celerybeat.pid ]; then
            kill $(cat /tmp/celerybeat.pid) 2>/dev/null || true
            rm -f /tmp/celerybeat.pid
        fi
        
        if [ -f /tmp/celeryworker.pid ]; then
            kill $(cat /tmp/celeryworker.pid) 2>/dev/null || true
            rm -f /tmp/celeryworker.pid
        fi
        
        echo -e "${GREEN}Scheduler stopped${NC}"
    fi
}

show_status() {
    echo -e "${GREEN}RENEC Scheduler Status${NC}"
    echo "========================"
    
    if command -v docker-compose &> /dev/null; then
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.scheduler.yml ps
    else
        # Check manual processes
        if [ -f /tmp/celerybeat.pid ] && ps -p $(cat /tmp/celerybeat.pid) > /dev/null 2>&1; then
            echo "Celery Beat: Running (PID: $(cat /tmp/celerybeat.pid))"
        else
            echo "Celery Beat: Not running"
        fi
        
        if [ -f /tmp/celeryworker.pid ] && ps -p $(cat /tmp/celeryworker.pid) > /dev/null 2>&1; then
            echo "Celery Worker: Running (PID: $(cat /tmp/celeryworker.pid))"
        else
            echo "Celery Worker: Not running"
        fi
    fi
    
    # Show scheduled tasks
    echo ""
    echo "Scheduled Tasks:"
    echo "- Daily probe: 2:00 AM (Mexico City time)"
    echo "- Freshness check: 6:00 AM (Mexico City time)"
    echo "- Weekly full harvest: Sunday 3:00 AM (Mexico City time)"
}

show_logs() {
    echo -e "${GREEN}Tailing scheduler logs...${NC}"
    
    if command -v docker-compose &> /dev/null; then
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.scheduler.yml logs -f --tail=100
    else
        # Tail log files
        if [ -d "$PROJECT_ROOT/logs" ]; then
            tail -f "$PROJECT_ROOT/logs/scheduler.log"
        else
            echo -e "${RED}No log files found${NC}"
        fi
    fi
}

test_harvest() {
    echo -e "${GREEN}Running test harvest...${NC}"
    
    cd "$PROJECT_ROOT"
    python3 -c "
from src.scheduler.daily_probe import trigger_harvest
result = trigger_harvest.delay(mode='probe')
print(f'Task ID: {result.id}')
print('Check Flower UI at http://localhost:5555 for task status')
"
}

# Main script
case "$1" in
    start)
        start_scheduler
        ;;
    stop)
        stop_scheduler
        ;;
    restart)
        stop_scheduler
        sleep 2
        start_scheduler
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        test_harvest
        ;;
    *)
        print_usage
        exit 1
        ;;
esac

exit 0