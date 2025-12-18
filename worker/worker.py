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

# Add server app to Python path - worker container has server code at /app/server
sys.path.insert(0, '/app/server')

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost")
TEMPORAL_PORT = int(os.getenv("TEMPORAL_PORT", "7233"))
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TASK_QUEUE = "eaichat-tasks"


async def run_worker():
    """Run the Temporal worker."""
    try:
        from temporalio.client import Client
        from temporalio.worker import Worker

        # Import workflows and activities from server app
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
        print(f"[INFO] Namespace: {TEMPORAL_NAMESPACE}")
        print(f"[INFO] Task Queue: {TASK_QUEUE}")
        
        client = await Client.connect(
            f"{TEMPORAL_HOST}:{TEMPORAL_PORT}",
            namespace=TEMPORAL_NAMESPACE
        )
        
        print("[SUCCESS] Connected to Temporal server")
        print(f"[INFO] Registering workflows: ProductSyncWorkflow, MultiPlatformSyncWorkflow, PlatformRefreshWorkflow")
        print(f"[INFO] Registering activities: fetch_and_index_from_platform, ensure_vector_collection, etc.")

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

        print("[SUCCESS] Worker initialized")
        print(f"[INFO] Worker polling task queue: {TASK_QUEUE}")
        print("[INFO] Worker started, waiting for tasks...")
        await worker.run()

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print(f"[ERROR] sys.path: {sys.path}")
        import traceback
        traceback.print_exc()
        print("[INFO] Falling back to placeholder worker")
        await fallback_worker()
    except Exception as e:
        print(f"[ERROR] Worker failed to start: {e}")
        import traceback
        traceback.print_exc()
        print("[INFO] Falling back to placeholder worker")
        await fallback_worker()


async def fallback_worker():
    """Fallback worker when Temporal dependencies are not available."""
    print("[WARN] Running fallback worker (no Temporal)")
    while True:
        await asyncio.sleep(30)
        print("[HEARTBEAT] Fallback worker alive but not processing tasks")


def main():
    print("=" * 60)
    print("eaichat Temporal Worker")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"sys.path: {sys.path[:3]}...")  # Show first 3 paths
    print("=" * 60)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
