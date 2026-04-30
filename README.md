cd camping-scanner

# venv 생성

- 파이선 버전 3.14.0
- 가상환경 생성

```shell
  python -m venv .venv
```

## 가상환경 활성화

### Windows

#.\.venv\Scripts\activate

### Mac

source .venv/bin/activate
deactivate

## 라이브러리 설치

- pip install fastapi uvicorn playwright jinja2
- playwright install chromium
- pip install pyinstaller
- pip install pyyaml
- pip install httpx
- pip install beautifulsoup4
- pip install 'uvicorn[standard]'
- pip install websockets
- pip install apscheduler
- pip install pytest pytest-asyncio pytest-mock
- pip install lxml
- pip install pystray Pillow

## GIT 사용법

git init

git add .
git commit -m "first commit"
git branch -M main
git push origin main

## 동일한 환경 배포용

- 새 컴퓨터에서 동일한 환경을 구축하기 위해 사용합니다.
  -- 기록: pip freeze > requirements.txt
  -- 설치: pip install -r requirements.txt
