"""
Spider management class for controlling Scrapy spiders via API.
"""
import asyncio
import subprocess
import signal
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import psutil

from .models import SpiderConfig, SpiderStatus, SpiderStats


class SpiderManager:
    """Manages spider processes and provides status/control interface."""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.config: Optional[SpiderConfig] = None
        self.status: SpiderStatus = SpiderStatus.IDLE
        self.stats: SpiderStats = SpiderStats()
        self.start_time: Optional[datetime] = None
        
    def is_running(self) -> bool:
        """Check if spider is currently running."""
        if self.process is None:
            return False
        
        try:
            # Check if process is still alive
            return self.process.poll() is None
        except Exception:
            return False
    
    async def start(self, config: SpiderConfig) -> bool:
        """Start spider with given configuration."""
        try:
            if self.is_running():
                return False
            
            # Build scrapy command
            cmd = [
                "python", "-m", "scrapy", "crawl", "renec",
                "-a", f"mode={config.mode.value}",
                "-a", f"max_depth={config.max_depth}",
                "-s", f"CONCURRENT_REQUESTS={config.concurrent_requests}",
                "-s", f"DOWNLOAD_DELAY={config.download_delay}",
                "-s", f"RETRY_TIMES={config.retry_times}",
                "-s", f"ROBOTSTXT_OBEY={str(config.respect_robots_txt).lower()}",
            ]
            
            # Add component filters
            enabled_components = [
                k for k, v in config.target_components.dict().items() if v
            ]
            if enabled_components:
                cmd.extend(["-a", f"components={','.join(enabled_components)}"])
            
            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="/Users/aldoruizluna/labspace/renec-harvester"
            )
            
            self.config = config
            self.status = SpiderStatus.RUNNING
            self.start_time = datetime.now()
            self._reset_stats()
            
            # Start background task to monitor process
            asyncio.create_task(self._monitor_process())
            
            return True
        
        except Exception as e:
            print(f"Failed to start spider: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the running spider."""
        try:
            if not self.is_running():
                return True
            
            # Gracefully terminate process
            if self.process:
                try:
                    # Send SIGTERM first
                    self.process.terminate()
                    
                    # Wait up to 10 seconds for graceful shutdown
                    try:
                        self.process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        # Force kill if still running
                        self.process.kill()
                        self.process.wait()
                
                except ProcessLookupError:
                    # Process already terminated
                    pass
            
            self.process = None
            self.status = SpiderStatus.IDLE
            
            return True
        
        except Exception as e:
            print(f"Failed to stop spider: {e}")
            return False
    
    async def pause(self) -> bool:
        """Pause the running spider."""
        try:
            if not self.is_running():
                return False
            
            if self.process:
                # Send SIGSTOP to pause process
                self.process.send_signal(signal.SIGSTOP)
                self.status = SpiderStatus.PAUSED
                return True
            
            return False
        
        except Exception as e:
            print(f"Failed to pause spider: {e}")
            return False
    
    async def resume(self) -> bool:
        """Resume a paused spider."""
        try:
            if self.status != SpiderStatus.PAUSED:
                return False
            
            if self.process:
                # Send SIGCONT to resume process
                self.process.send_signal(signal.SIGCONT)
                self.status = SpiderStatus.RUNNING
                return True
            
            return False
        
        except Exception as e:
            print(f"Failed to resume spider: {e}")
            return False
    
    async def reset(self) -> bool:
        """Reset spider state and clear cached data."""
        try:
            # Stop spider if running
            if self.is_running():
                await self.stop()
            
            # Reset state
            self.config = None
            self.status = SpiderStatus.IDLE
            self.start_time = None
            self._reset_stats()
            
            # TODO: Clear cached data from Redis/database
            
            return True
        
        except Exception as e:
            print(f"Failed to reset spider: {e}")
            return False
    
    def get_status(self) -> SpiderStatus:
        """Get current spider status."""
        if self.is_running():
            return self.status
        else:
            # Process died, update status
            self.status = SpiderStatus.IDLE
            return self.status
    
    def get_config(self) -> Optional[SpiderConfig]:
        """Get current spider configuration."""
        return self.config
    
    def get_stats(self) -> SpiderStats:
        """Get current spider statistics."""
        # Update runtime stats
        if self.start_time and self.is_running():
            uptime_delta = datetime.now() - self.start_time
            self.stats.uptime = str(uptime_delta).split('.')[0]  # Remove microseconds
        
        self.stats.status = self.get_status()
        
        # TODO: Get actual stats from spider/database
        # For now, return mock stats that change over time
        if self.is_running():
            runtime_minutes = (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0
            self.stats.total_requests = int(runtime_minutes * 45)  # Mock: 45 requests/minute
            self.stats.successful_requests = int(self.stats.total_requests * 0.95)  # 95% success rate
            self.stats.failed_requests = self.stats.total_requests - self.stats.successful_requests
            self.stats.items_scraped = int(runtime_minutes * 12)  # Mock: 12 items/minute
            self.stats.current_speed = 12.0
            self.stats.avg_response_time = 150.0
            self.stats.queue_size = max(0, 100 - int(runtime_minutes))
        
        return self.stats
    
    async def cleanup(self):
        """Cleanup resources when shutting down."""
        if self.is_running():
            await self.stop()
    
    async def _monitor_process(self):
        """Background task to monitor spider process."""
        while self.is_running():
            try:
                # Check if process is still alive
                if self.process and self.process.poll() is not None:
                    # Process terminated
                    self.status = SpiderStatus.IDLE
                    self.process = None
                    break
                
                await asyncio.sleep(5)  # Check every 5 seconds
            
            except Exception as e:
                print(f"Error monitoring process: {e}")
                break
    
    def _reset_stats(self):
        """Reset statistics to initial values."""
        self.stats = SpiderStats()
        if self.start_time:
            self.stats.start_time = self.start_time