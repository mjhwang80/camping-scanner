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

- pip install --upgrade pip
- pip install fastapi uvicorn playwright jinja2
- set PLAYWRIGHT_BROWSERS_PATH=pw-browsers
- export PLAYWRIGHT_BROWSERS_PATH=pw-browsers # 1회성 mac용
- playwright install chromium
- pip install pyinstaller
- pip install pyyaml
- pip install httpx
- pip install beautifulsoup4
- pip install 'uvicorn[standard]'
- pip install uvicorn uvloop httptools #위에 라인이 설치 안되면..
- pip install websockets
- pip install apscheduler
- pip install pytest pytest-asyncio pytest-mock
- pip install lxml
- pip install pystray Pillow
- pip install playwright-stealth
- pip install nodriver
- pip install nest_asyncio
- pip install python-telegram-bot

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

# 크롬 정보 추출

## 크롬 버전 알기

- 크롬 브라우저를 열고, 주소창에 명령어를 입력 : chrome://version
- 화면 중간쯤에 "프로필 경로" (Profile Path) 항목 찾음
- Mac 예시: /Users/사용자명/Library/Application Support/Google/Chrome/Default
- Windows 예시: C:\Users\사용자명\AppData\Local\Google\Chrome\User Data\Default

## 점검해야할 OS 문제

### 트레이 아이콘 알람

#### Windows

- **알림 및 작업 설정:** 윈도우 설정 > 시스템 > 알림에서 "앱 및 다른 보낸 사람의 알림 받기"가 켬 상태여야 합니다.
- **집중 지원 (방해금지 모드):** 집중 지원이 켜져 있으면 알림이 알림 센터로만 가고 화면에 나타나지 않습니다.
- **빌드 후 실행 시:** PyInstaller 등으로 빌드한 경우, 윈도우가 해당 실행 파일을 신뢰하지 않아 알림을 차단하는 경우가 있습니다. 이 경우 관리자 권한 실행을 시도해 보세요.

#### MAC

- **터미널/앱 권한:** osascript를 통해 알림을 보낼 때, 실행 주체(Terminal 또는 빌드된 앱)가 알림을 보낼 수 있는 권한이 있어야 합니다. 시스템 설정 > 알림 > 해당 앱(또는 스크립트 편집기/터미널)에서 알림 허용이 되어 있는지 확인하십시오.
- **스레드 주의:** icon.run()이 메인 스레드에서 실행되지 않으면 맥에서는 알림뿐만 아니라 트레이 아이콘 자체가 오작동할 확률이 매우 높습니다.
