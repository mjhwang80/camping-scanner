# Project: Camping Scanner (캠핑 스캐너)

이 문서는 Camping Scanner 프로젝트의 아키텍처, 개발 규칙, 및 워크플로우를 정의합니다.

## 1. 아키텍처 및 핵심 기술

- **Backend**: FastAPI (Python 3.14.0)
- **Monitoring/Automation**: Playwright (브라우저 자동화), APScheduler (스케줄링)
- **GUI**: Pystray (트레이 아이콘), Jinja2 (HTML 템플릿)
- **Build**: PyInstaller (단일 실행 파일 빌드)
- **Configuration**: YAML (`config/config.yaml`)

### 디렉토리 구조
- `app/`: 애플리케이션 핵심 로직
    - `core/`: 공통 유틸리티 (로거, 설정 로더, 트레이 아이콘 등)
    - `platforms/`: 플랫폼별 감시 로직 (Interpark, Foresttrip 등)
    - `services/`: 비즈니스 서비스
    - `templates/` & `static/`: 웹 UI 구성 요소
- `config/`: 외부 설정 파일
- `data/`: 플랫폼별 캠핑장 데이터 (XML)
- `logs/`: 애플리케이션 로그

## 2. 개발 및 설계 규칙

### 플랫폼 추가 가이드
- 새로운 플랫폼은 `app/platforms/base.py`의 `CampingMonitor` 인터페이스(추상 클래스)를 상속받아 구현해야 합니다.
- `check_availability(self, params: dict)` 메서드를 구현하여 빈자리 확인 로직을 작성합니다.
- 구현된 클래스는 `app/main.py`의 `start_monitor` 엔드포인트에서 조건부로 인스턴스화되도록 등록해야 합니다.

### 경로 처리 규칙
- 빌드된 환경(`.exe`)과 개발 환경에서 경로가 달라지는 문제를 방지하기 위해 `app/core/config_loader.py`의 함수를 사용합니다.
    - `get_resource_path(path)`: 실행 파일 내부(임시 폴더) 리소스 접근 시 사용.
    - `get_external_path(path)`: 실행 파일과 동일한 위치의 외부 파일(설정, 데이터) 접근 시 사용.

### 로깅 (Logging)
- `app/core/logger.py`에서 정의된 `logger`를 사용합니다.
- 웹소켓을 통해 실시간 로그를 UI에 전달하기 위해 전용 핸들러가 구성되어 있습니다.

### 설정 (Configuration)
- `config/config.yaml`은 런타임에 수정될 수 있으며, `save_config` 함수를 통해 반영합니다.

## 3. 코딩 컨벤션 및 스타일

- **이모티콘 사용 금지**: 코드, 주석, 로그 메시지, 문서(README 등) 및 UI의 모든 텍스트에서 이모티콘 사용을 금지합니다. 전문적인 기술 환경 유지를 위해 텍스트 기반의 마커(예: `[*]`, `[!]`, `[DONE]`)만 사용합니다.
- **언어**: 코드는 가급적 영문 변수/함수명을 사용하며, 주석과 로그는 명확한 한글 또는 영문을 사용합니다.

## 4. 개발 워크플로우

### 가상환경 및 의존성
- Python 3.14.0 버전 권장.
- `.venv` 가상환경 사용.
- 의존성 추가 시 `pip freeze > requirements.txt` 업데이트 필수.

### 테스트
- `pytest`, `pytest-asyncio`를 사용하여 비동기 로직을 테스트합니다.
- 플랫폼별 테스트는 `app/test/` 폴더 내에 작성합니다.

### 빌드 및 배포
- `python build.py`를 실행하여 PyInstaller 빌드를 수행합니다.
- 빌드 시 `pw-browsers` 경로가 올바르게 설정되어야 Playwright 브라우저가 포함됩니다.

## 4. 주의 사항

### 브라우저 자동화
- `playwright-stealth` 및 `--disable-blink-features=AutomationControlled` 옵션을 사용하여 자동화 탐지를 방지합니다.

### OS 종속성 (트레이 아이콘)
- `TrayIcon`은 메인 스레드에서 실행되어야 합니다 (특히 macOS 호환성을 위해).
- 트레이 아이콘 알림은 OS 설정에서 권한이 허용되어야 정상 작동합니다.

### 프로그램 만료
- `app/main.py`의 `check_expiration()` 함수에서 특정 날짜 이후 프로그램이 종료되도록 설정되어 있습니다. (현재 2026-07-30)
