from app.platforms.thankq import ThankQMonitor
#from app.platforms.camfit import CamfitMonitor

MONITORS = {
    "THANKQ": ThankQMonitor(),
    #"CAMFIT": CamfitMonitor()
}

async def run_monitoring(platform_type: str, params: dict):
    monitor = MONITORS.get(platform_type)
    if monitor:
        found = await monitor.check_availability(params)
        if found:
            # 여기서 알람 로직 호출 (Telegram 등)
            pass