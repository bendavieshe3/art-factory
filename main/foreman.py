"""
Foreman process for monitoring worker health and system reliability.
Handles edge cases like stalled workers and orphaned work.
"""
import os
import time
import signal
import threading
import logging
from datetime import timedelta
from django.utils import timezone

from .models import Worker, OrderItem, LogEntry

logger = logging.getLogger(__name__)


class Foreman:
    """
    Monitors worker health and handles failure recovery.
    Ensures system reliability and work continuity.
    """
    
    def __init__(self, check_interval=60):
        self.check_interval = check_interval
        self.is_running = True
        self.process_id = os.getpid()
        self.name = f"foreman-{int(time.time())}"
        
    def run(self):
        """Main foreman monitoring loop."""
        try:
            logger.info(f"Foreman {self.name} started (PID: {self.process_id})")
            
            LogEntry.objects.create(
                level='INFO',
                message=f'Foreman {self.name} started monitoring (PID: {self.process_id})',
                logger_name='foreman',
                extra_data={
                    'event_type': 'foreman_started',
                    'process_id': self.process_id
                }
            )
            
            while self.is_running:
                self.monitor_cycle()
                time.sleep(self.check_interval)
                
        except Exception as e:
            logger.error(f"Foreman {self.name} encountered error: {e}")
            LogEntry.objects.create(
                level='ERROR',
                message=f'Foreman {self.name} error: {str(e)}',
                logger_name='foreman',
                extra_data={
                    'event_type': 'foreman_error',
                    'error': str(e)
                }
            )
    
    def monitor_cycle(self):
        """Single monitoring cycle."""
        try:
            # 1. Check for stalled workers
            self.handle_stalled_workers()
            
            # 2. Check for orphaned work
            self.reassign_orphaned_work()
            
            # 3. Log system health
            self.log_system_status()
            
        except Exception as e:
            logger.error(f"Foreman monitor cycle error: {e}")
    
    def handle_stalled_workers(self):
        """Handle workers that have stopped responding."""
        stalled_workers = Worker.objects.filter(
            last_heartbeat__lt=timezone.now() - timedelta(minutes=3)
        )
        
        for worker in stalled_workers:
            logger.warning(f"Detected stalled worker: {worker.name} (PID: {worker.process_id})")
            
            # Try to kill the stalled process
            if self.process_exists(worker.process_id):
                try:
                    os.kill(worker.process_id, signal.SIGTERM)
                    logger.info(f"Killed stalled worker process {worker.process_id}")
                    
                    LogEntry.objects.create(
                        level='WARNING',
                        message=f'Killed stalled worker {worker.name} (PID: {worker.process_id})',
                        logger_name='foreman',
                        extra_data={
                            'event_type': 'worker_killed',
                            'worker_id': worker.id,
                            'process_id': worker.process_id
                        }
                    )
                    
                except ProcessLookupError:
                    logger.info(f"Worker process {worker.process_id} already dead")
                except PermissionError:
                    logger.error(f"Permission denied killing process {worker.process_id}")
                except Exception as e:
                    logger.error(f"Error killing worker process {worker.process_id}: {e}")
            
            # Reassign worker's claimed work
            self.reassign_worker_items(worker)
            
            # Remove worker record
            worker.delete()
            logger.info(f"Cleaned up stalled worker record: {worker.name}")
    
    def reassign_worker_items(self, worker):
        """Reassign OrderItems claimed by a failed worker."""
        assigned_items = OrderItem.objects.filter(
            assigned_worker=worker,
            status__in=['assigned', 'processing']
        )
        
        count = assigned_items.count()
        if count > 0:
            assigned_items.update(status='pending', assigned_worker=None)
            
            logger.info(f"Reassigned {count} items from failed worker {worker.name}")
            
            LogEntry.objects.create(
                level='INFO',
                message=f'Reassigned {count} items from failed worker {worker.name}',
                logger_name='foreman',
                extra_data={
                    'event_type': 'work_reassigned',
                    'worker_id': worker.id,
                    'items_reassigned': count
                }
            )
    
    def reassign_orphaned_work(self):
        """Find and reassign work that has no assigned worker."""
        orphaned_items = OrderItem.objects.filter(
            status='assigned',
            assigned_worker__isnull=True
        )
        
        count = orphaned_items.count()
        if count > 0:
            orphaned_items.update(status='pending')
            
            logger.warning(f"Found and reassigned {count} orphaned work items")
            
            LogEntry.objects.create(
                level='WARNING',
                message=f'Reassigned {count} orphaned work items',
                logger_name='foreman',
                extra_data={
                    'event_type': 'orphaned_work_reassigned',
                    'items_count': count
                }
            )
    
    def log_system_status(self):
        """Log current system health status."""
        try:
            # Count workers by status
            active_workers = Worker.objects.count()
            working_workers = Worker.objects.filter(status='working').count()
            
            # Count work items by status
            pending_items = OrderItem.objects.filter(status='pending').count()
            assigned_items = OrderItem.objects.filter(status='assigned').count()
            processing_items = OrderItem.objects.filter(status='processing').count()
            
            # Only log if there's interesting activity
            if active_workers > 0 or pending_items > 0:
                logger.info(
                    f"System status - Workers: {active_workers} ({working_workers} working), "
                    f"Work: {pending_items} pending, {assigned_items} assigned, {processing_items} processing"
                )
                
                LogEntry.objects.create(
                    level='INFO',
                    message=f'System health check - {active_workers} workers, {pending_items} pending items',
                    logger_name='foreman',
                    extra_data={
                        'event_type': 'health_check',
                        'active_workers': active_workers,
                        'working_workers': working_workers,
                        'pending_items': pending_items,
                        'assigned_items': assigned_items,
                        'processing_items': processing_items
                    }
                )
            
            # Check for concerning conditions
            if pending_items > 0 and active_workers == 0:
                logger.warning(f"Alert: {pending_items} pending items but no active workers")
                
                LogEntry.objects.create(
                    level='WARNING',
                    message=f'Alert: {pending_items} pending items but no active workers',
                    logger_name='foreman',
                    extra_data={
                        'event_type': 'no_workers_alert',
                        'pending_items': pending_items
                    }
                )
            
        except Exception as e:
            logger.error(f"Error logging system status: {e}")
    
    def process_exists(self, pid):
        """Check if a process with given PID exists."""
        try:
            os.kill(pid, 0)  # Signal 0 just checks if process exists
            return True
        except (OSError, ProcessLookupError):
            return False
    
    def stop(self):
        """Stop the foreman gracefully."""
        self.is_running = False
        logger.info(f"Foreman {self.name} stopping")
        
        LogEntry.objects.create(
            level='INFO',
            message=f'Foreman {self.name} stopped',
            logger_name='foreman',
            extra_data={'event_type': 'foreman_stopped'}
        )


# Global foreman instance for app integration
_foreman_instance = None
_foreman_thread = None


def start_foreman_if_needed():
    """Start foreman process if not already running."""
    global _foreman_instance, _foreman_thread
    
    if _foreman_instance is None or not _foreman_thread or not _foreman_thread.is_alive():
        try:
            _foreman_instance = Foreman()
            _foreman_thread = threading.Thread(target=_foreman_instance.run)
            _foreman_thread.daemon = True
            _foreman_thread.start()
            
            logger.info("Foreman started automatically")
            
        except Exception as e:
            logger.error(f"Failed to start foreman: {e}")


def stop_foreman():
    """Stop the foreman process."""
    global _foreman_instance
    
    if _foreman_instance:
        _foreman_instance.stop()
        _foreman_instance = None


def is_foreman_running():
    """Check if foreman is currently running."""
    global _foreman_thread
    return _foreman_thread and _foreman_thread.is_alive()