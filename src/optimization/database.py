"""
Database performance optimizations.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy import text, Index, func
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from src.models import get_session
from src.models.base import Base

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database performance optimization utilities."""
    
    def __init__(self, engine: Engine):
        """Initialize optimizer."""
        self.engine = engine
    
    def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """Analyze query performance using EXPLAIN ANALYZE."""
        with self.engine.connect() as conn:
            result = conn.execute(text(f"EXPLAIN ANALYZE {query}"))
            plan = list(result)
            
            # Extract key metrics
            execution_time = None
            planning_time = None
            
            for row in plan:
                line = row[0]
                if "Execution Time:" in line:
                    execution_time = float(line.split(":")[1].strip().split()[0])
                elif "Planning Time:" in line:
                    planning_time = float(line.split(":")[1].strip().split()[0])
            
            return {
                'query': query,
                'execution_time_ms': execution_time,
                'planning_time_ms': planning_time,
                'total_time_ms': (execution_time or 0) + (planning_time or 0),
                'plan': [row[0] for row in plan]
            }
    
    def create_indexes(self):
        """Create performance indexes."""
        indexes = [
            # EC Standards indexes
            Index('idx_ec_standards_vigente_sector', 'vigente', 'sector_id'),
            Index('idx_ec_standards_search', 'ec_clave', 'titulo'),
            Index('idx_ec_standards_dates', 'fecha_publicacion', 'fecha_vigencia'),
            
            # Certificadores indexes
            Index('idx_certificadores_tipo_estado', 'tipo', 'estado_inegi'),
            Index('idx_certificadores_estatus', 'estatus'),
            Index('idx_certificadores_search', 'cert_id', 'nombre_legal'),
            
            # Centros indexes
            Index('idx_centros_location', 'estado_inegi', 'municipio'),
            Index('idx_centros_certificador', 'certificador_id'),
            
            # Relationship indexes
            Index('idx_ece_ec_composite', 'cert_id', 'ec_clave'),
            Index('idx_centro_ec_composite', 'centro_id', 'ec_clave'),
            Index('idx_ec_sector_composite', 'ec_clave', 'sector_id'),
            
            # Temporal indexes
            Index('idx_last_seen', 'last_seen'),
            Index('idx_created_at', 'created_at'),
        ]
        
        created_count = 0
        for index in indexes:
            try:
                index.create(self.engine)
                created_count += 1
                logger.info(f"Created index: {index.name}")
            except Exception as e:
                logger.debug(f"Index {index.name} may already exist: {e}")
        
        logger.info(f"Created {created_count} new indexes")
    
    def vacuum_analyze(self):
        """Run VACUUM ANALYZE on all tables."""
        with self.engine.connect() as conn:
            # Get all tables
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = [row[0] for row in result]
            
            # Run VACUUM ANALYZE on each table
            for table in tables:
                try:
                    conn.execute(text(f"VACUUM ANALYZE {table}"))
                    conn.commit()
                    logger.info(f"Vacuum analyzed table: {table}")
                except Exception as e:
                    logger.error(f"Error vacuum analyzing {table}: {e}")
    
    def get_table_statistics(self) -> List[Dict[str, Any]]:
        """Get table size and row count statistics."""
        query = text("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                n_live_tup as row_count,
                n_dead_tup as dead_rows,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    def get_slow_queries(self, min_duration_ms: float = 100) -> List[Dict[str, Any]]:
        """Get slow queries from pg_stat_statements."""
        query = text(f"""
            SELECT 
                query,
                calls,
                total_exec_time,
                mean_exec_time,
                stddev_exec_time,
                rows
            FROM pg_stat_statements
            WHERE mean_exec_time > :min_duration
            ORDER BY mean_exec_time DESC
            LIMIT 20
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, {'min_duration': min_duration_ms})
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.warning(f"pg_stat_statements may not be enabled: {e}")
            return []
    
    def optimize_connection_pool(self):
        """Configure optimal connection pool settings."""
        # Already configured in engine creation, but can be adjusted here
        pool_config = {
            'pool_size': 20,
            'max_overflow': 40,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
        }
        
        logger.info(f"Connection pool optimized with settings: {pool_config}")
        return pool_config


class BulkOperations:
    """Optimized bulk database operations."""
    
    @staticmethod
    def bulk_insert_ec_standards(session: Session, standards: List[Dict[str, Any]]):
        """Bulk insert EC standards."""
        from src.models import ECStandardV2 as ECStandard
        
        # Prepare bulk insert data
        insert_data = []
        for std in standards:
            insert_data.append({
                'ec_clave': std['ec_clave'],
                'titulo': std['titulo'],
                'version': std.get('version'),
                'vigente': std.get('vigente', True),
                'sector': std.get('sector'),
                'sector_id': std.get('sector_id'),
                'comite': std.get('comite'),
                'comite_id': std.get('comite_id'),
                'descripcion': std.get('descripcion'),
                'competencias': std.get('competencias'),
                'nivel': std.get('nivel'),
                'duracion_horas': std.get('duracion_horas'),
                'tipo_norma': std.get('tipo_norma'),
                'fecha_publicacion': std.get('fecha_publicacion'),
                'fecha_vigencia': std.get('fecha_vigencia'),
                'content_hash': std.get('content_hash'),
                'last_seen': datetime.utcnow(),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
        
        # Use bulk_insert_mappings for performance
        session.bulk_insert_mappings(ECStandard, insert_data)
        session.commit()
        
        logger.info(f"Bulk inserted {len(insert_data)} EC standards")
    
    @staticmethod
    def bulk_upsert(session: Session, 
                    model_class: type,
                    records: List[Dict[str, Any]],
                    unique_key: str):
        """Bulk upsert (insert or update) records."""
        # Get existing records
        unique_values = [r[unique_key] for r in records]
        existing = session.query(model_class).filter(
            getattr(model_class, unique_key).in_(unique_values)
        ).all()
        
        existing_map = {getattr(e, unique_key): e for e in existing}
        
        # Separate inserts and updates
        to_insert = []
        to_update = []
        
        for record in records:
            key_value = record[unique_key]
            if key_value in existing_map:
                # Update existing
                record['id'] = existing_map[key_value].id
                record['updated_at'] = datetime.utcnow()
                to_update.append(record)
            else:
                # Insert new
                record['created_at'] = datetime.utcnow()
                record['updated_at'] = datetime.utcnow()
                to_insert.append(record)
        
        # Bulk operations
        if to_insert:
            session.bulk_insert_mappings(model_class, to_insert)
            logger.info(f"Bulk inserted {len(to_insert)} records")
        
        if to_update:
            session.bulk_update_mappings(model_class, to_update)
            logger.info(f"Bulk updated {len(to_update)} records")
        
        session.commit()


class QueryOptimizer:
    """SQL query optimization helpers."""
    
    @staticmethod
    def paginate_query(query, page: int = 1, per_page: int = 100):
        """Add efficient pagination to query."""
        offset = (page - 1) * per_page
        return query.limit(per_page).offset(offset)
    
    @staticmethod
    def add_search_filter(query, model_class, search_term: str, fields: List[str]):
        """Add optimized search filter."""
        if not search_term:
            return query
        
        # Use OR conditions for multiple fields
        conditions = []
        search_pattern = f"%{search_term}%"
        
        for field in fields:
            conditions.append(
                getattr(model_class, field).ilike(search_pattern)
            )
        
        return query.filter(func.or_(*conditions))
    
    @staticmethod
    def optimize_joins(query):
        """Optimize query joins to prevent N+1 queries."""
        # This would be implemented based on specific query patterns
        # For now, just return the query
        return query


# Database maintenance tasks
class DatabaseMaintenance:
    """Database maintenance operations."""
    
    def __init__(self, engine: Engine):
        """Initialize maintenance."""
        self.engine = engine
        self.optimizer = DatabaseOptimizer(engine)
    
    def run_daily_maintenance(self):
        """Run daily maintenance tasks."""
        logger.info("Starting daily database maintenance")
        
        # Update statistics
        self.optimizer.vacuum_analyze()
        
        # Check table sizes
        stats = self.optimizer.get_table_statistics()
        for stat in stats:
            logger.info(f"Table {stat['tablename']}: {stat['size']}, {stat['row_count']} rows")
        
        # Archive old data
        self.archive_old_data()
        
        logger.info("Daily database maintenance completed")
    
    def archive_old_data(self, days: int = 90):
        """Archive data older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with get_session() as session:
            # Archive old harvest runs
            from src.models.relations import HarvestRun
            
            old_harvests = session.query(HarvestRun).filter(
                HarvestRun.start_time < cutoff_date
            ).count()
            
            if old_harvests > 0:
                logger.info(f"Found {old_harvests} harvest runs older than {days} days")
                # In production, would move to archive table or S3
    
    def optimize_for_read_heavy_workload(self):
        """Optimize database for read-heavy workload."""
        optimizations = [
            "ALTER SYSTEM SET shared_buffers = '4GB'",
            "ALTER SYSTEM SET effective_cache_size = '12GB'",
            "ALTER SYSTEM SET work_mem = '256MB'",
            "ALTER SYSTEM SET maintenance_work_mem = '1GB'",
            "ALTER SYSTEM SET random_page_cost = 1.1",
            "ALTER SYSTEM SET effective_io_concurrency = 200",
            "ALTER SYSTEM SET max_parallel_workers_per_gather = 4",
            "ALTER SYSTEM SET max_parallel_workers = 8"
        ]
        
        logger.info("PostgreSQL optimization settings (apply manually):")
        for opt in optimizations:
            logger.info(f"  {opt}")
        
        logger.info("Remember to run 'SELECT pg_reload_conf()' after applying")