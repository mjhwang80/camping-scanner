#app/utils/download.py
import os
import sys
import requests
from urllib.parse import urlparse
import yt_dlp

from core.logger import logger as central_logger
import logging
logger = logging.getLogger("camping.download")
logger.propagate = True

def get_ffmpeg_path():
    """ PyInstaller 환경과 일반 실행 환경 모두 고려한 정확한 절대 경로 반환 """
    if getattr(sys, 'frozen', False):
        # 배포된 exe 실행 시: bin 폴더가 실행 파일(.exe)과 같은 위치에 있다고 가정
        base_path = os.path.dirname(sys.executable)
        return os.path.join(base_path, "bin")
    else:
        # 개발 환경: 본 download.py 파일 위치(app/utils/)를 기준으로 최상위 루트의 bin 폴더 계산
        # __file__은 현재 파일(download.py)의 절대 경로를 가리킵니다.
        current_dir = os.path.dirname(os.path.abspath(__file__)) # app/utils
        project_root = os.path.abspath(os.path.join(current_dir, "..", "..")) # camping-scanner/
        
        bin_path = os.path.join(project_root, "bin")
        return bin_path

def download_cdn_video(url, referer=None, output_dir="downloads"):
    """ CDN 파일을 다운로드하며, 선택적으로 레퍼러 헤더를 설정합니다. """
    os.makedirs(output_dir, exist_ok=True)
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path) or "downloaded_video.mp4"
    output_filename = os.path.join(output_dir, filename)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    # 사용자가 커스텀 레퍼러를 입력한 경우 헤더에 추가
    if referer:
        headers['Referer'] = referer
        logger.info(f"[CDN] 적용된 커스텀 Referer: {referer}")
    
    logger.info(f"[CDN 다운로드 시작] 파일명: {filename} / URL: {url}")
    try:
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 * 1024
            downloaded = 0
            last_reported_percent = -10 

            with open(output_filename, 'wb') as file:
                for data in response.iter_content(block_size):
                    file.write(data)
                    downloaded += len(data)
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        if percent >= last_reported_percent + 10:
                            #logger.info(f"[CDN 진행] {filename} -> {percent}% 완료 ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)")
                            print(f"[CDN 진행] {filename} -> {percent}% 완료 ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)")
                            last_reported_percent = percent
                    else:
                        if downloaded % (5 * 1024 * 1024) == 0:
                            logger.info(f"[CDN 진행] {filename} -> {downloaded // (1024*1024)}MB 다운로드 중...")

            logger.info(f"[CDN 완료] {filename} 저장 완료.")
        elif response.status_code == 403:
            logger.error(f"[CDN 에러] 403 Forbidden: 접근 권한 만료 또는 Referer 불일치 차단 가능성.")
        else:
            logger.error(f"[CDN 에러] HTTP 상태코드: {response.status_code}")
    except Exception as e:
        logger.error(f"[CDN 에러] 발생 원인: {e}")

def youtube_progress_hook(d):
    if d['status'] == 'downloading':
        filename = os.path.basename(d.get('filename', 'video.mp4'))
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '알 수 없음').strip()
        eta = d.get('_eta_str', '알 수 없음').strip()
        print(f"[YouTube 진행] {filename} -> 진행률: {percent} | 속도: {speed} | 남은 시간: {eta}")
    elif d['status'] == 'finished':
        filename = os.path.basename(d.get('filename', 'video.mp4'))
        logger.info(f"[YouTube 완료]  {filename} 스트림 다운로드 완료. 후처리 병합을 시작합니다.")

def download_youtube(url, download_type, referer=None, output_dir="downloads"):
    """ 유튜브 및 외부 미디어를 yt-dlp로 다운로드하며 선택적으로 레퍼러를 적용합니다. """
    os.makedirs(output_dir, exist_ok=True)
    
    ffmpeg_dir = get_ffmpeg_path()

    # [핵심] 현재 실행 중인 프로세스의 환경 변수(PATH) 맨 앞에 bin 폴더 경로를 강제 주입합니다.
    # 이렇게 하면 OS 단계에서 ffmpeg.exe와 ffprobe.exe를 무조건 가장 먼저 찾게 됩니다.
    if ffmpeg_dir and os.path.exists(ffmpeg_dir):
        current_path = os.environ.get('PATH', '')
        if ffmpeg_dir not in current_path:
            # 기존 PATH 맨 앞에 bin 경로를 붙여 OS가 최우선으로 탐색하게 만듭니다.
            os.environ['PATH'] = f"{ffmpeg_dir}{os.pathsep}{current_path}"
            logger.info(f"[OS PATH 임시 주입 적용] 경로: {ffmpeg_dir}")
    
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'progress_hooks': [youtube_progress_hook],
        'quiet': True,
        'no_warnings': True,
    }
    
    # yt-dlp 옵션에 커스텀 헤더/레퍼러 주입 규칙 적용
    if referer:
        ydl_opts['http_headers'] = {'Referer': referer}
        logger.info(f"[YouTube] 적용된 커스텀 Referer: {referer}")
    
    if download_type == "youtube_mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'

    if ffmpeg_dir:
        ffmpeg_binary = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
        ffmpeg_executable_path = os.path.join(ffmpeg_dir, ffmpeg_binary)
        
        # 실제 파일이 존재하는지 검증 후 세팅
        if os.path.exists(ffmpeg_executable_path):
            ydl_opts['ffmpeg_location'] = ffmpeg_executable_path
        else:
            logger.warning(f"[경고] 지정된 경로에 ffmpeg 파일이 없습니다: {ffmpeg_executable_path}")

    logger.info(f"[YouTube 작업 등록] 유형: {download_type} / URL: {url}")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logger.info(f"[YouTube 최종 완료]  모든 다운로드 및 인코딩 프로세스가 종료되었습니다.")
    except Exception as e:
        logger.error(f"[YouTube 에러] 실패 원인: {e}")