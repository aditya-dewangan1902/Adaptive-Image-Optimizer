"""Worker process entry point."""

from apps.worker.consumers import process_queue_loop
from src.infrastructure.telemetry.logging import logger

if __name__ == "__main__":
    logger.info("Starting Image Optimizer Worker service...")
    process_queue_loop()
