import logging
from apscheduler.jobstores.base import JobLookupError

# 로거 설정
logger = logging.getLogger("camping.termination")

async def handle_monitoring_stop(scheduler, ws_manager, params, found_sites):
    """
    빈자리 발견 시 감시 종료 조건(findNextRun)을 체크하고 
    스케줄러 작업 삭제 및 UI 제거 명령을 수행합니다.
    
    :param scheduler: AsyncIOScheduler 객체 (APScheduler)
    :param ws_manager: WebSocketManager 객체 (실시간 UI 업데이트용)
    :param params: 사용자가 요청한 감시 파라미터 (dict)
    :param found_sites: 크롤링 결과 발견된 사이트 리스트 (list)
    """
    
    # 1. 종료 조건 및 정보 추출
    # findNextRun이 'N'인 경우에만 빈자리 발견 시 자동 종료 처리
    find_next_run = params.get("findNextRun", "Y")
    job_id = params.get("watchUuid")
    campsite_name = params.get("campsiteName", "알 수 없는 캠핑장")

    # 빈자리가 발견되었고, 1회성 감시(N)로 설정된 경우
    if found_sites and find_next_run == "N":
        logger.info(f"🚩 [자동 종료 프로세스 시작] {campsite_name} (ID: {job_id})")
        
        try:
            # 2. APScheduler에서 해당 작업 제거 (더 이상 크롤링하지 않음)
            # Java의 scheduler.cancel() 또는 task.stop()과 동일한 역할
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
                logger.info(f"✅ 스케줄러에서 작업 제거 완료: {job_id}")
            
            # 3. 웹 프론트엔드(UI)에 목록 삭제 명령 전송
            # 브라우저의 JavaScript는 이 메시지를 받아 해당 테이블 행(tr)을 삭제함
            await ws_manager.broadcast({
                "messageType": "remove_monitor",
                "data": {
                    "uuid": job_id,
                    "msg": f"[{campsite_name}] 빈자리를 발견하여 감시가 성공적으로 종료되었습니다."
                }
            })
            
        except JobLookupError:
            # 이미 삭제되었거나 존재하지 않는 ID일 경우의 예외 처리
            logger.warning(f"⚠️ 삭제하려는 작업을 찾을 수 없습니다 (이미 삭제됨): {job_id}")
        except Exception as e:
            logger.error(f"감시 종료 처리 중 오류 발생: {e}")
    else:
        # 감시 유지(findNextRun == 'Y')인 경우 로그만 남김
        logger.debug(f"ℹ️ {campsite_name} 감시를 계속 유지합니다 (findNextRun: {find_next_run})")