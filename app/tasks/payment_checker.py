"""
Payment deadline checker task.

This module provides a background task to automatically delete proposals
with expired payment deadlines (24 hours after creation).
"""
import logging
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.services.proposal_service import ProposalService


logger = logging.getLogger(__name__)


def check_and_delete_expired_proposals():
    """
    Check for proposals with expired payment deadlines and delete them.

    This function should be called periodically (e.g., every hour) by a scheduler.
    """
    db = SessionLocal()
    try:
        deleted_count = ProposalService.delete_expired_proposals(db)

        if deleted_count > 0:
            logger.info(
                f"Deleted {deleted_count} proposal(s) with expired payment deadlines "
                f"at {datetime.now(timezone.utc)}"
            )
        else:
            logger.debug(f"No expired proposals found at {datetime.now(timezone.utc)}")

        return deleted_count

    except Exception as e:
        logger.error(f"Error checking expired proposals: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


# Example usage with APScheduler (optional)
"""
from apscheduler.schedulers.background import BackgroundScheduler

def start_scheduler():
    scheduler = BackgroundScheduler()

    # Run every hour
    scheduler.add_job(
        check_and_delete_expired_proposals,
        'interval',
        hours=1,
        id='payment_deadline_checker'
    )

    scheduler.start()
    logger.info("Payment checker scheduler started")

    return scheduler
"""

# Example usage with FastAPI background tasks
"""
from fastapi import BackgroundTasks

@app.on_event("startup")
async def startup_event():
    # Option 1: Use APScheduler
    # start_scheduler()

    # Option 2: Use FastAPI BackgroundTasks on each request
    # (Not recommended for scheduled tasks)
    pass
"""
