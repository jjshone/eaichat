"""
Temporal Workflows for eaichat - Updated Architecture
====================================================

Workflows for:
- Product sync from platform connectors
- Scheduled batch indexing
- Platform-specific reindexing
""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities
with workflow.unsafe.imports_passed_through():
    from .activities import (
        fetch_and_index_from_platform,
        ensure_vector_collection,
        get_collection_stats,
        delete_platform_products,
        send_langfuse_trace,
    )


@workflow.defn
class ProductSyncWorkflow:
    """
    Workflow to sync products from a platform connector to vector DB.
    Can be scheduled to run periodically.
    """

    @workflow.run
    async def run(self, platform: str = "fakestore", batch_size: int = 50) -> dict:
        workflow.logger.info(f"Starting product sync: platform={platform}, batch={batch_size}")

        # Ensure collection exists
        await workflow.execute_activity(
            ensure_vector_collection,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        # Trace start event
        await workflow.execute_activity(
            send_langfuse_trace,
            {
                "name": "product_sync_start",
                "metadata": {"platform": platform, "batch_size": batch_size},
                "tags": ["product_sync", platform],
            },
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Fetch and index products
        result = await workflow.execute_activity(
            fetch_and_index_from_platform,
            {"platform": platform, "batch_size": batch_size},
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=10),
                backoff_coefficient=2.0,
            ),
            heartbeat_timeout=timedelta(seconds=30),
        )

        # Trace completion
        await workflow.execute_activity(
            send_langfuse_trace,
            {
                "name": "product_sync_complete",
                "metadata": {"platform": platform, "result": result},
                "tags": ["product_sync", platform, result["status"]],
            },
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info(f"Sync complete: {result}")
        return result


@workflow.defn
class MultiPlatformSyncWorkflow:
    """
    Workflow to sync products from multiple platforms in parallel.
    """

    @workflow.run
    async def run(self, platforms: list[str], batch_size: int = 50) -> dict:
        workflow.logger.info(f"Starting multi-platform sync: {platforms}")

        # Ensure collection
        await workflow.execute_activity(
            ensure_vector_collection,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Run syncs in parallel
        sync_tasks = []
        for platform in platforms:
            task = workflow.execute_activity(
                fetch_and_index_from_platform,
                {"platform": platform, "batch_size": batch_size},
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )
            sync_tasks.append(task)

        results = await workflow.asyncio.gather(*sync_tasks)

        total_indexed = sum(r.get("indexed", 0) for r in results)

        return {
            "status": "completed",
            "platforms": platforms,
            "total_indexed": total_indexed,
            "results": results,
        }


@workflow.defn
class PlatformRefreshWorkflow:
    """
    Workflow to delete and re-index products from a specific platform.
    Useful for full refresh when platform data changes.
    """

    @workflow.run
    async def run(self, platform: str, batch_size: int = 50) -> dict:
        workflow.logger.info(f"Refreshing platform: {platform}")

        # Delete existing products
        delete_result = await workflow.execute_activity(
            delete_platform_products,
            platform,
            start_to_close_timeout=timedelta(minutes=2),
        )

        workflow.logger.info(f"Deleted {delete_result.get('deleted', 0)} products")

        # Re-index fresh data
        index_result = await workflow.execute_activity(
            fetch_and_index_from_platform,
            {"platform": platform, "batch_size": batch_size},
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        return {
            "status": "completed",
            "platform": platform,
            "deleted": delete_result.get("deleted", 0),
            "indexed": index_result.get("indexed", 0),
        }
