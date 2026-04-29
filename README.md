cd camping-scanner

# venv 생성

python -m venv venv

# 가상환경 활성화(Windows)

#.\venv\Scripts\activate

pip install fastapi uvicorn playwright jinja2

# 크롤링에 필요한 브라우저 바이너리 설치

playwright install chromium

#배포 라이브러리
pip install pyinstaller
pip install pyyaml
pip install httpx
pip install beautifulsoup4
pip install 'uvicorn[standard]'
pip install websockets
pip install apscheduler
pip install pytest pytest-asyncio pytest-mock
pip install lxml
