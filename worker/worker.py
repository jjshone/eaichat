"""
Temporal Worker for eaichat
===========================

This worker connects to Temporal server and executes workflows/activities.
Run with: python worker.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add server to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost")
TEMPORAL_PORT = int(os.getenv("TEMPORAL_PORT", "7233"))
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TASK_QUEUE = "eaichat-tasks"


async def run_worker():
    """Run the Temporal worker."""
    try:
        from temporalio.client import Client
        from temporalio.worker import Worker

        # Import workflows and activities
        from app.workflows.workflows import (
            ProductSyncWorkflow,
            MultiPlatformSyncWorkflow,
            PlatformRefreshWorkflow,
        )
        from app.workflows.activities import (
            fetch_and_index_from_platform,
            ensure_vector_collection,
            get_collection_stats,
            delete_platform_products,
            send_langfuse_trace,
        )

        print(f"[INFO] Connecting to Temporal at {TEMPORAL_HOST}:{TEMPORAL_PORT}")
        client = await Client.connect(
            f"{TEMPORAL_HOST}:{TEMPORAL_PORT}",
            namespace=TEMPORAL_NAMESPACE
        )

        print(f"[INFO] Starting worker for task queue: {TASK_QUEUE}")
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[
                ProductSyncWorkflow,
                MultiPlatformSyncWorkflow,
                PlatformRefreshWorkflow,
            ],
            activities=[
                fetch_and_index_from_platform,
                ensure_vector_collection,
                get_collection_stats,
                delete_platform_products,
                send_langfuse_trace,
            ],
        )

        print("[INFO] Worker started, waiting for tasks...")
        await worker.run()

    except ImportError as e:
        print(f"[WARN] Missing dependencies for Temporal worker: {e}")
        print("[INFO] Running in fallback mode (placeholder)")
        await fallback_worker()
    except Exception as e:
        print(f"[ERROR] Worker failed: {e}")
        import traceback
        traceback.print_exc()
        await fallback_worker()


async def fallback_worker():
    """Fallback worker when Temporal dependencies are not available."""
    print("[INFO] Running fallback worker (no Temporal)")
    while True:
        await asyncio.sleep(30)
        print("[HEARTBEAT] Worker alive")


def main():
    print("=" * 50)
    print("eaichat Temporal Worker")
    print("=" * 50)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
