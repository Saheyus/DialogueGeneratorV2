"""Gestionnaire d'état des jobs de génération en cours."""
import uuid
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Literal
import logging

logger = logging.getLogger(__name__)


class GenerationJobManager:
    """Gestionnaire en mémoire des jobs de génération avec TTL et cleanup automatique."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Args:
            ttl_seconds: Durée de vie d'un job en secondes (default: 1h)
        """
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds = ttl_seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        self._tasks: Dict[str, asyncio.Task] = {}
    
    def create_job(self, params: dict) -> str:
        """
        Crée un nouveau job de génération.
        
        Args:
            params: Paramètres de génération (sera passé au service)
        
        Returns:
            job_id: UUID du job créé
        """
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        self._jobs[job_id] = {
            'job_id': job_id,
            'status': 'queued',
            'params': params,
            'result': None,
            'error': None,
            'cancelled': False,
            'done_event': asyncio.Event(),
            'created_at': now.isoformat(),
            'updated_at': now.isoformat(),
            'expires_at': (now + timedelta(seconds=self._ttl_seconds)).isoformat(),
        }
        
        logger.info(f"Job {job_id} created", extra={'job_id': job_id})
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les infos d'un job."""
        job = self._jobs.get(job_id)
        if job and self._is_expired(job):
            self._remove_job(job_id)
            return None
        return job
    
    def update_status(
        self,
        job_id: str,
        status: Literal["queued", "running", "completed", "error", "cancelled"],
        result: Optional[dict] = None,
        error: Optional[str] = None
    ) -> None:
        """Met à jour le statut d'un job."""
        job = self._jobs.get(job_id)
        if not job:
            logger.warning(f"Attempted to update non-existent job {job_id}")
            return
        
        job['status'] = status
        job['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        if result is not None:
            job['result'] = result
        if error is not None:
            job['error'] = error
        
        if status in ('completed', 'error', 'cancelled'):
            done_event = job.get('done_event')
            if isinstance(done_event, asyncio.Event):
                done_event.set()
        
        logger.info(f"Job {job_id} status updated to {status}", extra={'job_id': job_id, 'status': status})
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Marque un job comme annulé.
        
        Returns:
            True si le job a été annulé, False sinon (job inexistant ou déjà terminé)
        """
        job = self._jobs.get(job_id)
        if not job:
            logger.warning(f"Attempted to cancel non-existent job {job_id}")
            return False
        
        if job['status'] in ('completed', 'error', 'cancelled'):
            logger.info(f"Job {job_id} already finished, cannot cancel")
            return False
        
        job['cancelled'] = True
        job['status'] = 'cancelled'
        job['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
        logger.info(f"Job {job_id} cancelled", extra={'job_id': job_id})
        return True
    
    def is_cancelled(self, job_id: str) -> bool:
        """Vérifie si un job a été annulé."""
        job = self._jobs.get(job_id)
        return job['cancelled'] if job else False
    
    def _is_expired(self, job: Dict[str, Any]) -> bool:
        """Vérifie si un job a expiré."""
        expires_at = datetime.fromisoformat(job['expires_at'])
        return datetime.now(timezone.utc) > expires_at
    
    def _remove_job(self, job_id: str) -> None:
        """Supprime un job (appelé par cleanup)."""
        if job_id in self._jobs:
            del self._jobs[job_id]
        if job_id in self._tasks:
            del self._tasks[job_id]
            logger.debug(f"Job {job_id} removed from memory")
    
    def register_task(self, job_id: str, task: asyncio.Task) -> None:
        """Enregistre la tâche de génération pour permettre l'annulation."""
        self._tasks[job_id] = task
    
    def unregister_task(self, job_id: str) -> None:
        """Supprime la référence à la tâche de génération."""
        if job_id in self._tasks:
            del self._tasks[job_id]
    
    async def wait_for_completion(self, job_id: str, timeout_seconds: int = 10) -> bool:
        """Attend la fin d'un job (completed/error/cancelled) avec timeout."""
        job = self._jobs.get(job_id)
        if not job:
            return False
        
        done_event = job.get('done_event')
        if not isinstance(done_event, asyncio.Event):
            return False
        
        try:
            await asyncio.wait_for(done_event.wait(), timeout=timeout_seconds)
            return True
        except asyncio.TimeoutError:
            return False
    
    async def start_cleanup_task(self) -> None:
        """Démarre la tâche de nettoyage périodique des jobs expirés."""
        if self._cleanup_task is not None:
            logger.warning("Cleanup task already running")
            return
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Cleanup task started")
    
    async def stop_cleanup_task(self) -> None:
        """Arrête la tâche de nettoyage."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Cleanup task stopped")
    
    async def _cleanup_loop(self) -> None:
        """Boucle de nettoyage des jobs expirés (toutes les 5 minutes)."""
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes
                await self._cleanup_expired_jobs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_expired_jobs(self) -> None:
        """Supprime les jobs expirés."""
        now = datetime.now(timezone.utc)
        expired_jobs = [
            job_id
            for job_id, job in self._jobs.items()
            if datetime.fromisoformat(job['expires_at']) < now
        ]
        
        for job_id in expired_jobs:
            self._remove_job(job_id)
        
        if expired_jobs:
            logger.info(f"Cleaned up {len(expired_jobs)} expired jobs")


# Instance globale (singleton)
_job_manager: Optional[GenerationJobManager] = None


def get_job_manager() -> GenerationJobManager:
    """Récupère l'instance singleton du job manager."""
    global _job_manager
    if _job_manager is None:
        _job_manager = GenerationJobManager()
    return _job_manager
