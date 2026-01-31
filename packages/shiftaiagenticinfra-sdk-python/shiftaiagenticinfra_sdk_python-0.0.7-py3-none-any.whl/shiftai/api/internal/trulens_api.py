"""
API for Eval metrics operations.

This is an internal/admin API for observability and quality assessment.
Not part of normal client flows - use for monitoring and evaluation purposes only.
"""

from typing import Dict, Any
from uuid import UUID
from ...http import HttpClient


class EvalApi:
    """API for Eval metrics operations."""
    
    def __init__(self, http_client: HttpClient):
        self._http_client = http_client
    
    async def generate_metrics_for_session(
        self,
        conversation_id: UUID
    ) -> Dict[str, Any]:
        """
        Generate metrics for a specific completed session.
        
        POST /api/eval/sessions/{conversationId}/generate-metrics
        
        Args:
            conversation_id: UUID of the completed conversation
            
        Returns:
            Dictionary with processing status
        """
        self._http_client.ensure_authenticated()

        return await self._http_client.post_map(
            f"/api/eval/sessions/{conversation_id}/generate-metrics",
            {}
        )
    
    async def generate_metrics_for_all_sessions(self) -> Dict[str, Any]:
        """
        Generate metrics for all completed sessions in the project.
        
        POST /api/eval/sessions/generate-metrics
        
        Returns:
            Dictionary with processing status
        """
        self._http_client.ensure_authenticated()

        return await self._http_client.post_map(
            "/api/eval/sessions/generate-metrics",
            {}
        )
    
    async def generate_metrics_for_all_conversations(self) -> Dict[str, Any]:
        """
        Generate metrics for all conversations (admin - no auth required).
        
        POST /api/eval/sessions/generate-metrics-all
        
        Returns:
            Dictionary with job ID for progress tracking
        """
        return await self._http_client.post_map_without_auth(
            "/api/eval/sessions/generate-metrics-all",
            {}
        )
    
    async def get_batch_progress(self, job_id: str) -> Dict[str, Any]:
        """
        Get progress for a batch metrics generation job (admin - no auth required).
        
        GET /api/eval/sessions/generate-metrics-all/{jobId}/progress
        
        Args:
            job_id: The job ID returned from generate_metrics_for_all_conversations
            
        Returns:
            Dictionary with current progress information
        """
        return await self._http_client.get_map_without_auth(
            f"/api/eval/sessions/generate-metrics-all/{job_id}/progress"
        )

