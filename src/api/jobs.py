import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from src.db import SessionLocal, Job
from src.core.scrape import run_scraper
from src.core.analyze import run_analysis
from src.core.generate import run_email_generation
from src.core.send import send_emails
from src.llm.bakeoff import run_model_comparison
from src.utils.logging import logger

# Global registries for running asyncio tasks and SSE listener queues
running_tasks: Dict[int, asyncio.Task] = {}
job_listeners: Dict[int, List[asyncio.Queue]] = {}

async def notify_listeners(job_id: int, payload: Dict[str, Any]):
    """
    Pushes status and progress payload updates to all registered listeners for a job.
    """
    if job_id in job_listeners:
        for queue in job_listeners[job_id]:
            await queue.put(payload)

async def execute_job(job_id: int):
    """
    Executes a pipeline job in the background, updating database state,
    notifying listeners, and handling cancellation or failures.
    """
    # Register the task in the global registry
    running_tasks[job_id] = asyncio.current_task()

    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        db.close()
        logger.error("Attempted to execute non-existent job", job_id=job_id)
        return
        
    if job.status == "cancelled":
        db.close()
        logger.info("Job was cancelled before execution started", job_id=job_id)
        return

    # Update job state to running
    job.status = "running"
    job.started_at = datetime.utcnow()
    db.commit()

    # Create progress callback
    async def progress_callback(done: int, total: int, message: Optional[str] = None):
        # We need a separate session or local refresh to prevent transaction lockups
        local_db = SessionLocal()
        try:
            local_job = local_db.query(Job).filter(Job.id == job_id).first()
            if local_job:
                local_job.done = done
                local_job.total = total
                local_job.status = "running"
                local_db.commit()
                
                # Notify listeners
                await notify_listeners(job_id, {
                    "id": job_id,
                    "type": local_job.type,
                    "status": "running",
                    "done": done,
                    "total": total,
                    "message": message,
                    "error": None
                })
        except Exception as e:
            logger.error("Failed to update job progress in database", error=str(e), job_id=job_id)
        finally:
            local_db.close()

    try:
        # Determine parameters
        params = job.params or {}
        limit = params.get("limit")
        
        logger.info("Starting pipeline job execution", job_id=job_id, job_type=job.type, params=params)

        # Trigger corresponding pipeline orchestrator
        if job.type == "scrape":
            stats = await run_scraper(db, limit=limit, progress_callback=progress_callback)
            job.done = stats.get("total", 0)
            job.total = stats.get("total", 0)
        elif job.type == "analyze":
            stats = await run_analysis(db, limit=limit, progress_callback=progress_callback)
            job.done = stats.get("total", 0)
            job.total = stats.get("total", 0)
        elif job.type == "generate":
            model = params.get("model")
            provider = params.get("provider")
            stats = await run_email_generation(
                db, limit=limit, model_override=model, 
                provider_override=provider, progress_callback=progress_callback
            )
            job.done = stats.get("total", 0)
            job.total = stats.get("total", 0)
        elif job.type == "send":
            dry_run = params.get("dry_run")
            stats = await send_emails(db, limit=limit, dry_run=dry_run, progress_callback=progress_callback)
            job.done = stats.get("total", 0)
            job.total = stats.get("total", 0)
        elif job.type == "bakeoff":
            sample = params.get("sample", 5)
            models = params.get("models")
            
            # Simple progress update (0/1 -> 1/1)
            await progress_callback(0, 1)
            await run_model_comparison(db, sample_size=sample, models=models)
            await progress_callback(1, 1)
            job.done = 1
            job.total = 1
        elif job.type == "pipeline":
            # Stage 1: Scrape
            logger.info("Pipeline Step 1/3: Running website scraper...", job_id=job_id)
            await progress_callback(0, 3, "Step 1/3: Scraping pending website content...")
            await run_scraper(db, limit=limit)
            
            # Stage 2: Analyze
            logger.info("Pipeline Step 2/3: Running website analysis...", job_id=job_id)
            await progress_callback(1, 3, "Step 2/3: Analyzing crawled sites & metadata...")
            await run_analysis(db, limit=limit)
            
            # Stage 3: Generate
            logger.info("Pipeline Step 3/3: Running email generation...", job_id=job_id)
            await progress_callback(2, 3, "Step 3/3: Drafting cold emails with grounding validation...")
            model = params.get("model")
            provider = params.get("provider")
            await run_email_generation(
                db, limit=limit, model_override=model, 
                provider_override=provider
            )
            
            await progress_callback(3, 3, "Pipeline complete! Drafts generated successfully.")
            job.done = 3
            job.total = 3
        else:
            raise ValueError(f"Unknown pipeline job type: {job.type}")

        # Complete job
        job.status = "completed"
        job.finished_at = datetime.utcnow()
        db.commit()

        await notify_listeners(job_id, {
            "id": job_id,
            "type": job.type,
            "status": "completed",
            "done": job.done,
            "total": job.total,
            "error": None
        })
        logger.info("Pipeline job completed successfully", job_id=job_id)

    except asyncio.CancelledError:
        # Task was cancelled cooperatively
        logger.warning("Pipeline job execution cancelled cooperatively", job_id=job_id)
        # Re-fetch lead using local session to avoid transaction dirty states
        local_db = SessionLocal()
        try:
            local_job = local_db.query(Job).filter(Job.id == job_id).first()
            if local_job:
                local_job.status = "cancelled"
                local_job.finished_at = datetime.utcnow()
                local_db.commit()
                
            await notify_listeners(job_id, {
                "id": job_id,
                "type": job.type if local_job else "unknown",
                "status": "cancelled",
                "done": local_job.done if local_job else 0,
                "total": local_job.total if local_job else 0,
                "error": "Job cancelled by user request"
            })
        finally:
            local_db.close()
        raise

    except Exception as e:
        logger.error("Pipeline job failed with exception", error=str(e), job_id=job_id)
        job.status = "failed"
        job.error = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()

        await notify_listeners(job_id, {
            "id": job_id,
            "type": job.type,
            "status": "failed",
            "done": job.done,
            "total": job.total,
            "error": str(e)
        })

    finally:
        db.close()
        # Clean up global registry reference
        if job_id in running_tasks:
            del running_tasks[job_id]

def enqueue_job(job_type: str, params: Dict[str, Any], db: Session, background_tasks) -> Job:
    """
    Creates a Job in database, enqueues it, and spawns the background worker task.
    """
    job = Job(
        type=job_type,
        status="queued",
        done=0,
        total=0,
        params=params,
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue task via FastAPI's BackgroundTasks
    background_tasks.add_task(execute_job, job.id)

    logger.info("Job successfully queued via BackgroundTasks", job_id=job.id, job_type=job_type)
    return job
