import os
import sys
import requests
from urllib.parse import urlparse
import yt_dlp
import logging

logger = logging.getLogger("camping.download")

def find_ffmpeg_in_venv():
    bin_dir = os.path.dirname(sys.executable)
    if os.path.exists(os.path.join(bin_dir, "ffmpeg.exe")) or os.path.exists(os.path.join(bin_dir, "ffmpeg")):
        return bin_dir
    venv_root = os.path.abspath(os.path.join(bin_dir, ".."))
    for root, dirs, files in os.walk(venv_root):
        if "ffmpeg.exe" in files or "ffmpeg" in files:
            return root
    return None

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
                            logger.info(f"[CDN 진행] {filename} -> {percent}% 완료 ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)")
                            last_reported_percent = percent
                    else:
                        if downloaded % (5 * 1024 * 1024) == 0:
                            logger.info(f"[CDN 진행] {filename} -> {downloaded // (1024*1024)}MB 다운로드 중...")

            logger.info(f"[CDN 완료] 📥 {filename} 저장 완료.")
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
        logger.info(f"[YouTube 진행] {filename} -> 진행률: {percent} | 속도: {speed} | 남은 시간: {eta}")
    elif d['status'] == 'finished':
        filename = os.path.basename(d.get('filename', 'video.mp4'))
        logger.info(f"[YouTube 완료] 🔄 {filename} 스트림 다운로드 완료. 후처리 병합을 시작합니다.")

def download_youtube(url, download_type, referer=None, output_dir="downloads"):
    """ 유튜브 및 외부 미디어를 yt-dlp로 다운로드하며 선택적으로 레퍼러를 적용합니다. """
    os.makedirs(output_dir, exist_ok=True)
    ffmpeg_dir = find_ffmpeg_in_venv()
    
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
                'key': 'FFMPEGExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'

    if ffmpeg_dir:
        ydl_opts['ffmpeg_location'] = ffmpeg_dir

    logger.info(f"[YouTube 작업 등록] 유형: {download_type} / URL: {url}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logger.info(f"[YouTube 최종 완료] 🎉 모든 다운로드 및 인코딩 프로세스가 종료되었습니다.")
    except Exception as e:
        logger.error(f"[YouTube 에러] 실패 원인: {e}")