"""Worker task execution definitions."""

from src.domain.models.job import Job
from src.services.optimization_service import OptimizationService


def execute_optimization_task(job: Job) -> dict:
    """Execute optimization job in worker process."""
    svc = OptimizationService()
    result = svc.run_job(job)
    return {
        "job_id": result.job_id,
        "status": result.status.value,
        "output_path": result.output_path,
        "output_size_bytes": result.output_size_bytes,
        "duration_ms": result.duration_ms,
    }
