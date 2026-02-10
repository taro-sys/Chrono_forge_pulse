"""Background task manager for async operations"""
import asyncio
from typing import Dict, Any, Callable
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BackgroundTaskManager:
    """Manage background tasks for training and processing"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
    
    def create_task(self, task_id: str, task_name: str) -> Dict[str, Any]:
        """Create a new background task"""
        task = {
            "task_id": task_id,
            "task_name": task_name,
            "status": TaskStatus.PENDING,
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }
        self.tasks[task_id] = task
        return task
    
    def update_status(self, task_id: str, status: TaskStatus, 
                      result: Any = None, error: str = None):
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status
            
            if status == TaskStatus.PROCESSING:
                self.tasks[task_id]["started_at"] = datetime.utcnow()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                self.tasks[task_id]["completed_at"] = datetime.utcnow()
                self.tasks[task_id]["result"] = result
                self.tasks[task_id]["error"] = error
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        return self.tasks.get(task_id, {})
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove old completed tasks"""
        current_time = datetime.utcnow()
        to_remove = []
        
        for task_id, task in self.tasks.items():
            if task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                if task["completed_at"]:
                    age = (current_time - task["completed_at"]).total_seconds() / 3600
                    if age > max_age_hours:
                        to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]


# Global task manager instance
task_manager = BackgroundTaskManager()
