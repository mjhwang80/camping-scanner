from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

# 전역 스케줄러 설정 (Java의 TaskScheduler 역할)
scheduler = AsyncIOScheduler(
    jobstores={'default': MemoryJobStore()},
    timezone="Asia/Seoul"
)

def start_scheduler():
    if not scheduler.running:
        scheduler.start()