"""
Temporal Workflows for eaichat
==============================

Defines workflows for:
- Product reindexing (scheduled sync)
- Chat processing
- Data export (GDPR)
"""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities
with workflow.unsafe.imports_passed_through():
    from .activities import (
        fetch_and_index_products,
        reindex_products_batch,
        get_reindex_checkpoint,
        update_reindex_checkpoint,
        send_langfuse_event,
    )


@workflow.defn
class ProductSyncWorkflow:
    """
    Workflow to sync products from external API and index to Qdrant.
    Scheduled to run periodically via Temporal.
    """

    @workflow.run
    async def run(self, source: str = "fakestore") -> dict:
        workflow.logger.info(f"Starting product sync from {source}")

        # Send telemetry event
        await workflow.execute_activity(
            send_langfuse_event,
            {"event": "product_sync_started", "source": source},
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Fetch and index products
        result = await workflow.execute_activity(
            fetch_and_index_products,
            source,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=10),
            ),
        )

        # Send completion event
        await workflow.execute_activity(
            send_langfuse_event,
            {"event": "product_sync_completed", "result": result},
            start_to_close_timeout=timedelta(seconds=30),
        )

        return {"status": "completed", "indexed": result}


@workflow.defn
class ReindexWorkflow:
    """
    Workflow for full product reindexing with checkpointing.
    Supports resume on failure.
    """

    @workflow.run
    async def run(self, batch_size: int = 32) -> dict:
        workflow.logger.info(f"Starting reindex workflow (batch_size={batch_size})")

        total_indexed = 0
        offset = await workflow.execute_activity(
            get_reindex_checkpoint,
            "products",
            start_to_close_timeout=timedelta(seconds=30),
        )

        while True:
            # Process batch
            result = await workflow.execute_activity(
                reindex_products_batch,
                {"batch_size": batch_size, "offset": offset},
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                ),
            )

            if result["count"] == 0:
                break

            total_indexed += result["count"]
            offset = result["last_id"]

            # Update checkpoint
            await workflow.execute_activity(
                update_reindex_checkpoint,
                {"collection": "products", "last_id": offset},
                start_to_close_timeout=timedelta(seconds=30),
            )

        return {"status": "completed", "total_indexed": total_indexed}


@workflow.defn
class ChatWorkflow:
    """
    Workflow for processing chat messages with RAG.
    """

    @workflow.run
    async def run(self, message: str, user_id: int, session_id: str) -> dict:
        workflow.logger.info(f"Processing chat for user {user_id}")

        # This would orchestrate:
        # 1. Vector search for relevant products
        # 2. LLM call with context
        # 3. Tool execution (add to cart, etc.)
        # 4. Save message to DB
        # 5. Send telemetry

        # Placeholder for now - will be implemented with full chat service
        return {
            "status": "processed",
            "message": message,
            "user_id": user_id,
            "session_id": session_id,
        }
