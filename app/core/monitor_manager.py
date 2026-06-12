#app/core/monitor_manager.py

import logging
logger = logging.getLogger("camping.manager")
class MonitorManager:
    _monitors = {}

    @classmethod
    def add(cls, job_id, monitor):
        cls._monitors[job_id] = monitor
        logger.info(f"[MonitorManager] 모니터 등록 완료: {job_id}")

    @classmethod
    def get(cls, job_id):
        return cls._monitors.get(job_id)

    @classmethod
    def remove(cls, job_id):
        if job_id in cls._monitors:
            del cls._monitors[job_id]
            logger.info(f"[MonitorManager] 모니터 제거 완료: {job_id}")

    @classmethod
    def get_all(cls):
        return cls._monitors