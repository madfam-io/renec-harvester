"""
Daily probe workflow for automated RENEC harvesting.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import select, func

from src.models import get_session, HarvestRun
from src.models import ECStandardV2 as ECStandard
from src.models import CertificadorV2 as Certificador
from src.cli.commands.harvest import run_harvest

logger = logging.getLogger(__name__)

# Initialize Celery
app = Celery('renec_harvester',
             broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
             backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Mexico_City',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # 50 minutes soft limit
)

# Schedule configuration
app.conf.beat_schedule = {
    'daily-harvest': {
        'task': 'src.scheduler.daily_probe.probe_and_harvest',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
        'options': {'queue': 'harvest'}
    },
    'freshness-check': {
        'task': 'src.scheduler.daily_probe.check_data_freshness',
        'schedule': crontab(hour=6, minute=0),  # Run at 6 AM daily
        'options': {'queue': 'monitoring'}
    },
    'weekly-full-harvest': {
        'task': 'src.scheduler.daily_probe.full_harvest',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
        'options': {'queue': 'harvest'}
    }
}


@app.task(name='src.scheduler.daily_probe.probe_and_harvest')
def probe_and_harvest() -> Dict[str, Any]:
    """
    Daily probe to check for updates and harvest changed content.
    """
    harvest_id = f"daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Starting daily probe harvest: {harvest_id}")
    
    # Record harvest start
    with get_session() as session:
        harvest_run = HarvestRun(
            harvest_id=harvest_id,
            start_time=datetime.utcnow(),
            mode='probe',
            spider_name='renec',
            status='running',
            metadata={'type': 'daily_probe'}
        )
        session.add(harvest_run)
        session.commit()
        run_id = harvest_run.id
    
    try:
        # Run targeted harvest for frequently changing components
        result = run_harvest(
            mode='harvest',
            components=['ec_standards', 'certificadores'],
            max_pages=500,  # Limit pages for daily run
            concurrent_requests=5
        )
        
        # Update harvest record
        with get_session() as session:
            harvest_run = session.get(HarvestRun, run_id)
            harvest_run.end_time = datetime.utcnow()
            harvest_run.items_scraped = result.get('items_scraped', 0)
            harvest_run.pages_crawled = result.get('pages_crawled', 0)
            harvest_run.errors = result.get('errors', 0)
            harvest_run.status = 'completed'
            harvest_run.metadata.update(result)
            session.commit()
        
        logger.info(f"Daily probe completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Daily probe failed: {str(e)}")
        
        # Update harvest record with error
        with get_session() as session:
            harvest_run = session.get(HarvestRun, run_id)
            harvest_run.end_time = datetime.utcnow()
            harvest_run.status = 'failed'
            harvest_run.metadata['error'] = str(e)
            session.commit()
        
        raise


@app.task(name='src.scheduler.daily_probe.check_data_freshness')
def check_data_freshness() -> Dict[str, Any]:
    """
    Check data freshness and alert on stale data.
    """
    logger.info("Checking data freshness")
    
    freshness_threshold = datetime.utcnow() - timedelta(days=7)
    alerts = []
    
    with get_session() as session:
        # Check EC Standards
        stale_ec_count = session.query(func.count(ECStandard.id)).filter(
            ECStandard.last_seen < freshness_threshold
        ).scalar()
        
        if stale_ec_count > 0:
            alerts.append({
                'entity': 'ec_standards',
                'stale_count': stale_ec_count,
                'message': f'{stale_ec_count} EC standards not updated in 7+ days'
            })
        
        # Check Certificadores
        stale_cert_count = session.query(func.count(Certificador.id)).filter(
            Certificador.last_seen < freshness_threshold
        ).scalar()
        
        if stale_cert_count > 0:
            alerts.append({
                'entity': 'certificadores',
                'stale_count': stale_cert_count,
                'message': f'{stale_cert_count} certificadores not updated in 7+ days'
            })
        
        # Get overall statistics
        total_ec = session.query(func.count(ECStandard.id)).scalar()
        total_cert = session.query(func.count(Certificador.id)).scalar()
        
        # Get last harvest info
        last_harvest = session.query(HarvestRun).filter(
            HarvestRun.status == 'completed'
        ).order_by(HarvestRun.start_time.desc()).first()
    
    result = {
        'check_time': datetime.utcnow().isoformat(),
        'freshness_threshold_days': 7,
        'statistics': {
            'total_ec_standards': total_ec,
            'total_certificadores': total_cert,
            'stale_ec_standards': stale_ec_count,
            'stale_certificadores': stale_cert_count
        },
        'alerts': alerts,
        'last_successful_harvest': {
            'harvest_id': last_harvest.harvest_id if last_harvest else None,
            'time': last_harvest.start_time.isoformat() if last_harvest else None,
            'items': last_harvest.items_scraped if last_harvest else 0
        }
    }
    
    # Log alerts
    if alerts:
        logger.warning(f"Data freshness alerts: {json.dumps(alerts)}")
    else:
        logger.info("All data is fresh")
    
    return result


@app.task(name='src.scheduler.daily_probe.full_harvest')
def full_harvest() -> Dict[str, Any]:
    """
    Weekly full harvest of all components.
    """
    harvest_id = f"weekly_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Starting weekly full harvest: {harvest_id}")
    
    # Record harvest start
    with get_session() as session:
        harvest_run = HarvestRun(
            harvest_id=harvest_id,
            start_time=datetime.utcnow(),
            mode='harvest',
            spider_name='renec',
            status='running',
            metadata={'type': 'weekly_full'}
        )
        session.add(harvest_run)
        session.commit()
        run_id = harvest_run.id
    
    try:
        # Run full harvest
        result = run_harvest(
            mode='harvest',
            components='all',  # All components
            concurrent_requests=10  # More aggressive for weekly run
        )
        
        # Update harvest record
        with get_session() as session:
            harvest_run = session.get(HarvestRun, run_id)
            harvest_run.end_time = datetime.utcnow()
            harvest_run.items_scraped = result.get('items_scraped', 0)
            harvest_run.pages_crawled = result.get('pages_crawled', 0)
            harvest_run.errors = result.get('errors', 0)
            harvest_run.status = 'completed'
            harvest_run.metadata.update(result)
            session.commit()
        
        logger.info(f"Weekly full harvest completed: {result}")
        
        # Trigger export after successful harvest
        export_artifacts.delay(harvest_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Weekly full harvest failed: {str(e)}")
        
        # Update harvest record with error
        with get_session() as session:
            harvest_run = session.get(HarvestRun, run_id)
            harvest_run.end_time = datetime.utcnow()
            harvest_run.status = 'failed'
            harvest_run.metadata['error'] = str(e)
            session.commit()
        
        raise


@app.task(name='src.scheduler.daily_probe.export_artifacts')
def export_artifacts(harvest_id: str) -> Dict[str, Any]:
    """
    Export harvest artifacts after successful harvest.
    """
    logger.info(f"Exporting artifacts for harvest: {harvest_id}")
    
    from src.export import DataExporter
    
    exporter = DataExporter()
    export_dir = f"artifacts/exports/{harvest_id}"
    os.makedirs(export_dir, exist_ok=True)
    
    try:
        # Export to multiple formats
        results = {
            'json': exporter.export_to_json(f"{export_dir}/data.json"),
            'csv': exporter.export_to_csv(export_dir),
            'graph': exporter.export_graph_json(f"{export_dir}/graph.json"),
            'denormalized': exporter.export_denormalized_json(f"{export_dir}/denormalized.json")
        }
        
        # Create bundle
        bundle_path = exporter.export_bundle(
            f"{export_dir}/bundle_{harvest_id}.zip",
            formats=['json', 'csv', 'graph', 'denormalized']
        )
        results['bundle'] = bundle_path
        
        logger.info(f"Export completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise


# Manual trigger functions
@app.task(name='src.scheduler.daily_probe.trigger_harvest')
def trigger_harvest(mode: str = 'probe', components: Optional[list] = None) -> Dict[str, Any]:
    """
    Manually trigger a harvest.
    """
    harvest_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Manually triggered harvest: {harvest_id}")
    
    if mode == 'probe':
        return probe_and_harvest()
    else:
        return full_harvest()


if __name__ == '__main__':
    # For testing
    print("Daily probe scheduler configured")
    print("Schedule:")
    for name, config in app.conf.beat_schedule.items():
        print(f"  - {name}: {config['schedule']}")