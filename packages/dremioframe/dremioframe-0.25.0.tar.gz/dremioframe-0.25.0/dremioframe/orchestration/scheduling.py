from typing import Optional
from .pipeline import Pipeline
from .backend import BaseBackend

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
except ImportError:
    BackgroundScheduler = None

def schedule_pipeline(pipeline: Pipeline, interval_seconds: float = None, cron: str = None, blocking: bool = True, job_store_url: str = None):
    """
    Schedules a pipeline to run periodically using APScheduler.
    
    Args:
        pipeline: The pipeline to run.
        interval_seconds: Run every X seconds.
        cron: Run according to cron expression (5 fields).
        blocking: If True, blocks the main thread. If False, runs in background.
        job_store_url: Optional SQLAlchemy connection string to persist jobs (e.g. sqlite:///jobs.db).
    """
    if BackgroundScheduler is None:
        raise ImportError("apscheduler is required for scheduling. Install with `pip install dremioframe[scheduler]`")

    if not interval_seconds and not cron:
        raise ValueError("Must specify either interval_seconds or cron.")

    # Select scheduler
    scheduler_cls = BlockingScheduler if blocking else BackgroundScheduler
    
    jobstores = {}
    if job_store_url:
        jobstores['default'] = SQLAlchemyJobStore(url=job_store_url)
        
    scheduler = scheduler_cls(jobstores=jobstores)
    
    # Define trigger
    trigger = None
    if cron:
        # APScheduler cron trigger
        # cron string: "* * * * *" -> minute, hour, day, month, day_of_week
        # We need to parse it or pass as kwargs. 
        # APScheduler CronTrigger.from_crontab() is convenient if available, or we split manually.
        trigger = CronTrigger.from_crontab(cron)
    else:
        trigger = IntervalTrigger(seconds=interval_seconds)

    # Add job
    # We wrap pipeline.run to catch exceptions
    def job_func():
        print(f"Starting scheduled run for {pipeline.name}")
        try:
            pipeline.run()
        except Exception as e:
            print(f"Scheduled run failed: {e}")

    scheduler.add_job(job_func, trigger, id=pipeline.name, replace_existing=True)
    
    print(f"Scheduler started for pipeline {pipeline.name}. Mode: {'Blocking' if blocking else 'Background'}")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

