import os
import sys
import yaml

def get_external_path(relative_path):
    """
    빌드된 환경에서 실행 파일(.exe)과 동일한 위치의 외부 경로를 반환합니다.
    개발 환경에서는 프로젝트 루트를 반환합니다.
    """
    if hasattr(sys, '_MEIPASS'):
        # 빌드 후: 실행 파일(.exe)이 위치한 실제 디렉토리 기준
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, relative_path)
    
    # 개발 시: 프로젝트 루트 기준
    return os.path.join(os.path.abspath("."), relative_path)

def get_resource_path(relative_path):
    """실행 파일 내부(임시폴더) 또는 개발 루트에서 절대 경로를 반환합니다."""
    if hasattr(sys, '_MEIPASS'):
        # 빌드 후: .exe 실행 시 임시 폴더 경로 (_MEIPASS)
        return os.path.join(sys._MEIPASS, relative_path)
    # 개발 시: 프로젝트 루트 기준
    return os.path.join(os.path.abspath("."), relative_path)

def load_config():
    # 'config/config.yaml' 경로를 안전하게 계산합니다.
    config_path = get_resource_path(os.path.join("config", "config.yaml"))
    
    if not os.path.exists(config_path):
        # 만약 빌드본 외부(실행파일과 같은 위치)의 설정파일을 우선하고 싶다면 아래 로직 추가
        exe_dir_config = os.path.join(os.path.dirname(sys.executable), "config", "config.yaml")
        if os.path.exists(exe_dir_config):
            config_path = exe_dir_config
        else:
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_full_config():
    """파일에서 전체 설정을 다시 읽어옵니다."""
    config_path = get_external_path(os.path.join("config", "config.yaml"))
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_config(new_data_dict):
    """전달받은 데이터를 config.yaml에 저장하고 전역 CONFIG를 업데이트합니다."""
    config_path = get_external_path(os.path.join("config", "config.yaml"))
    
    # 1. 기존 데이터 로드
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            current_data = yaml.safe_load(f) or {}
    else:
        current_data = {}

    # 2. 데이터 업데이트
    for key, value in new_data_dict.items():
        current_data[key] = value
        
    # 3. 파일 쓰기
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(current_data, f, allow_unicode=True, sort_keys=False)
    
    # 4. 전역 객체 업데이트 (즉시 반영)
    CONFIG.update(new_data_dict)


CONFIG = load_config()